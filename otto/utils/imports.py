from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeGuard

from frappe.utils import get_bench_path

if TYPE_CHECKING:
	from collections.abc import Callable
	from types import ModuleType


def get_import_path(fn: Callable) -> str:
	"""
	Get the import path for a function.

	If the function is in an app, then the import path is the dotted module path.
	The function can be regularly imported without loading the file.
		eg: otto.tools.bash_tool.bash

	If the function is not in an app, then the import path is the file path.
	The file must be loaded to import the function.
		eg: /home/user/projects/tools/package/bash_tool.py:bash


	Note: this function does not guarantee that the function will be imported
	from the same location, it saves the path of where the function is defined.
	"""
	apps_path = Path(get_bench_path()) / "apps"
	fn_path = Path(inspect.getfile(fn)).absolute()
	fn_path = Path(fn_path)

	if fn_path.is_relative_to(apps_path):
		return f"{fn.__module__}.{fn.__qualname__}"

	return f"{fn_path.as_posix()}:{fn.__qualname__}"


def import_fn(path: str) -> Callable:
	"""
	The argument `path` can be of the following forms:
	- dotted path: "path.to.module.function"
	- file path: "path/to/module.py:function"

	In both cases, module is first imported and then the function is returned
	from the module.
	"""

	parts = path.rsplit(":", maxsplit=1)
	if len(parts) != 2:
		parts = path.rsplit(".", maxsplit=1)

	if len(parts) != 2:
		raise ValueError(f"Invalid path provided: {path}")

	module_path, name = parts
	if not name.isidentifier():
		raise ValueError(f"Invalid function name found: {name} in path: {path}")

	module = import_module(path)
	fn = getattr(module, name, None)

	if fn is None:
		raise ValueError(f"Could not find function '{name}' in module '{module_path}'")

	if not callable(fn):
		raise ValueError(f"Imported attribute '{name}' from module '{module_path}' is not callable")

	return fn


def import_module(path: str) -> ModuleType:
	"""Imports module from dot separated path or file path"""

	if is_fs_path(path):
		return import_from_fs_path(path)

	if not is_dotted_path(path):
		raise ValueError(f"Invalid path provided: {path}")

	# Else import from dotted path
	return importlib.import_module(path)


def import_from_fs_path(path: str | Path) -> ModuleType:
	"""
	Provided path may be a path to a single file or to a package

	If provided path is to a package, then the module name is the name of the
	package (i.e. the name of the directory containing the __init__.py file)

	If provided path is to a single file, then the module name is the name of
	the file (i.e. the name of the file without the extension)

	If provided path is to a __init__.py file, then the module name will be then
	name its parent directory.
	"""
	from importlib.util import module_from_spec, spec_from_file_location

	if isinstance(path, str):
		path = Path(path)

	if path.is_dir():
		path = path / "__init__.py"  # Assume package

	if not path.exists():
		raise FileNotFoundError(f"Incorrect path provided. File not found: {path}")

	name = path.name
	if name == "__init__.py":
		name = path.parent.name
	else:
		name = name.removesuffix(".py")

	spec = spec_from_file_location(name, path)
	if spec is None:
		raise ImportError(f"Could not create module spec for {path}")

	module = module_from_spec(spec)
	if spec.loader is None:
		raise ImportError(f"Could not get loader for {path}")

	spec.loader.exec_module(module)
	return module


def is_fs_path(path: Any) -> TypeGuard[str]:
	import os

	if not isinstance(path, str) or not path:
		return False

	if os.path.sep in path or (os.path.altsep and os.path.altsep in path):
		return True
	if os.path.isabs(path):
		return True
	if os.path.exists(path):
		return True

	return False


def is_dotted_path(path: Any) -> TypeGuard[str]:
	"""
	Check if the provided path is a Python module path (dot separated and valid Python identifiers).
	"""
	if not isinstance(path, str) or not path:
		return False

	parts = path.split(".")
	for part in parts:
		if not part.isidentifier():
			return False
	return len(parts) > 1
