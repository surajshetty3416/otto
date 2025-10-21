# Mostly from https://github.com/phillipdupuis/pydantic-to-typescript/blob/master/pydantic2ts/cli/script.py
from __future__ import annotations

import importlib
import inspect
import json
import os
import subprocess
import sys
import tempfile
from contextlib import ExitStack, contextmanager
from importlib.util import module_from_spec, spec_from_file_location
from typing import (
	TYPE_CHECKING,
	Any,
)
from uuid import uuid4

from pydantic import BaseModel, create_model

if TYPE_CHECKING:  # pragma: no cover
	from collections.abc import Generator
	from types import ModuleType

	from pydantic.config import ConfigDict


_MASTER = "_Master_"
_USELESS_ENUM_DESCRIPTION = "An enumeration."
_USELESS_STR_DESCRIPTION = inspect.getdoc(str)


def _import_module(path: str) -> ModuleType:
	"""
	Helper which allows modules to be specified by either dotted path notation or by filepath.

	If we import by filepath, we must also assign a name to it and add it to sys.modules BEFORE
	calling 'spec.loader.exec_module' because there is code in pydantic which requires that the
	definition exist in sys.modules under that name.
	"""
	try:
		if os.path.exists(path):
			name = uuid4().hex
			spec = spec_from_file_location(name, path, submodule_search_locations=[])
			assert spec is not None, f"spec_from_file_location failed for {path}"
			module = module_from_spec(spec)
			sys.modules[name] = module
			assert spec.loader is not None, f"loader is None for {path}"
			spec.loader.exec_module(module)
			return module
		return importlib.import_module(path)
	except Exception as e:
		raise e


def _is_submodule(obj: Any, module_name: str) -> bool:
	"""
	Return true if an object is a submodule
	"""
	return inspect.ismodule(obj) and getattr(obj, "__name__", "").startswith(f"{module_name}.")


def _is_pydantic_model(obj: Any) -> bool:
	"""
	Return true if an object is a 'concrete' pydantic V2 model.
	"""
	if not inspect.isclass(obj) or obj is BaseModel or not issubclass(obj, BaseModel):
		return False

	generic_metadata = getattr(obj, "__pydantic_generic_metadata__", {})
	generic_parameters = generic_metadata.get("parameters")
	return not generic_parameters


def _is_nullable(schema: dict[str, Any]) -> bool:
	"""
	Return true if a JSON schema has 'null' as one of its types.
	"""
	if schema.get("type") == "null":
		return True
	if isinstance(schema.get("type"), list) and "null" in schema["type"]:
		return True
	if isinstance(schema.get("anyOf"), list):
		return any(_is_nullable(s) for s in schema["anyOf"])
	return False


def _get_model_config(model: type[Any]) -> ConfigDict:
	"""
	Return the 'config' for a pydantic model.
	In version 1 of pydantic, this is a class. In version 2, it's a dictionary.
	"""
	return model.model_config


def _get_model_json_schema(model: type[Any]) -> dict[str, Any]:
	"""
	Generate the JSON schema for a pydantic model.
	"""
	return model.model_json_schema(mode="serialization")


def _extract_pydantic_models(module: ModuleType) -> list[type]:
	"""
	Given a module, return a list of the pydantic models contained within it.
	"""
	models: list[type] = []
	module_name = module.__name__

	for _, model in inspect.getmembers(module, _is_pydantic_model):
		models.append(model)

	for _, submodule in inspect.getmembers(module, lambda obj: _is_submodule(obj, module_name)):
		models.extend(_extract_pydantic_models(submodule))

	return models


def _clean_json_schema(schema: dict[str, Any], model: Any = None) -> None:
	"""
	Clean up the resulting JSON schemas via the following steps:

	1) Get rid of descriptions that are auto-generated and just add noise:
		- "An enumeration." for Enums
		- `inspect.getdoc(str)` for Literal types
	2) Remove titles from JSON schema properties.
		If we don't do this, each property will have its own interface in the
		resulting typescript file (which is a LOT of unnecessary noise).
	3) If it's a V1 model, ensure that nullability is properly represented.
		https://github.com/pydantic/pydantic/issues/1270
	"""
	description = schema.get("description")

	if (
		"enum" in schema and description == _USELESS_ENUM_DESCRIPTION
	) or description == _USELESS_STR_DESCRIPTION:
		del schema["description"]

	properties: dict[str, dict[str, Any]] = schema.get("properties", {})

	for prop in properties.values():
		prop.pop("title", None)


@contextmanager
def _schema_generation_overrides(
	model: type[Any],
) -> Generator[None, None, None]:
	"""
	Temporarily override the 'extra' setting for a model,
	changing it to 'forbid' unless it was EXPLICITLY set to 'allow'.
	This prevents '[k: string]: any' from automatically being added to every interface.
	"""
	revert: dict[str, Any] = {}
	config = _get_model_config(model)
	try:
		if isinstance(config, dict):
			if config.get("extra") != "allow":
				revert["extra"] = config.get("extra")
				config["extra"] = "forbid"
		else:
			if config.extra != "allow":
				revert["extra"] = config.extra
				config.extra = "forbid"  # type: ignore
		yield
	finally:
		for key, value in revert.items():
			if isinstance(config, dict):
				config[key] = value
			else:
				setattr(config, key, value)


def _generate_json_schema(models: list[type]) -> dict[str, Any]:
	"""
	Create a top-level '_Master_' model with references to each of the actual models.
	Generate the schema for this model, which will include the schemas for all the
	nested models. Then clean up the schema.
	"""
	with ExitStack() as stack:
		models_by_name: dict[str, type] = {}
		models_as_fields: dict[str, tuple[type, Any]] = {}

		for model in models:
			stack.enter_context(_schema_generation_overrides(model))
			name = model.__name__
			models_by_name[name] = model
			models_as_fields[name] = (model, ...)

		master_model = create_model(_MASTER, **models_as_fields)  # type: ignore
		master_schema = _get_model_json_schema(master_model)

		defs_key = "$defs" if "$defs" in master_schema else "definitions"
		defs: dict[str, Any] = master_schema.get(defs_key, {})

		for name, schema in defs.items():
			_clean_json_schema(schema, models_by_name.get(name))

		return master_schema


def _jsonc_to_typescript(jsonsc: dict[str, Any]):
	with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as temp_file:
		json.dump(jsonsc, temp_file, indent=2)
		temp_file_path = temp_file.name

	# Call json2ts on the temporary file
	try:
		result = subprocess.run(
			["npx", "json2ts", "-i", temp_file_path], capture_output=True, text=True, check=True
		)

		os.unlink(temp_file_path)
		# Clean up the temporary file

		return result.stdout

	except subprocess.CalledProcessError:
		# Clean up the temporary file even if there's an error
		os.unlink(temp_file_path)

	return None


def _ts_type_str_to_dict(ts_types: str) -> dict[str, str]:
	# Convert the TypeScript interfaces string into a dictionary
	interfaces_dict = {}

	# Split the string by 'export interface' to get individual interface definitions
	interface_blocks = ts_types.split("export interface ")[1:]  # Skip the first empty element

	for block in interface_blocks:
		# Extract the interface name (everything before the first opening brace)
		if (name_end := block.find("{")) == -1:
			continue

		interface_name = block[:name_end].strip()

		# Get the full interface definition including the opening and closing braces
		if (closing_brace_pos := block.rfind("}")) == -1:
			continue

		# Find the end of the interface (the first closing brace followed by a newline or end of string)
		if (interface_end := block.find("\n", closing_brace_pos)) == -1:
			interface_end = len(block)

		# Reconstruct the full interface definition
		interfaces_dict[interface_name] = f"export interface {block[: interface_end + 1]}".strip()
	del interfaces_dict[_MASTER]

	return interfaces_dict


def get_pydantic_types(
	path: str,
) -> dict[str, str]:
	"""
	Convert the pydantic models in a python module into typescript interfaces.
	"""
	module = _import_module(path)
	models = _extract_pydantic_models(module)
	if not models:
		return {}

	jsonsc = _generate_json_schema(models)
	if (ts_types := _jsonc_to_typescript(jsonsc)) is None:
		return {}

	return _ts_type_str_to_dict(ts_types)
