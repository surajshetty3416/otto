from __future__ import annotations

from typing import TYPE_CHECKING

import frappe

import otto
from otto.lib.types import ToolSchema, ToolSchemaParameters
from otto.tools.types import ToolDefinition
from otto.utils import get_title_from_slug
from otto.utils.imports import get_import_path, import_module

"""
The same tool may be installed through sync_tool and sync_assistant if the assistant
makes use of the tool. The `installed_tools` list is used to track the tools that have
been installed to prevent wasted effort in reinstalling.

sync_tool is idempotent so multiple calls should not be an issue
"""
installed_tools: list[str] = []

if TYPE_CHECKING:
	from types import ModuleType


def sync_tools(modules: list[ModuleType | str]) -> None:
	for module in modules:
		try:
			sync_tool(module)
		except Exception as e:
			otto.log_error(
				title="Error syncing tool",
				assistant_module=str(module),
			)
			if frappe.conf.developer_mode:
				print(e)


def sync_otto_tools() -> None:
	from otto.tools import bash_tool

	sync_tools([bash_tool])


def sync_tool(module: ModuleType | str) -> str | None:
	# Import module if a string path is provided
	if isinstance(module, str):
		module = import_module(module)

	tool_definition = _get_tool_definition(module)
	if tool_definition["dev_mode_only"] and not frappe.conf.developer_mode:
		return None

	if tool_definition["name"] in installed_tools and not frappe.flags.in_test:
		return tool_definition["name"]

	tool_name = _ensure_tool(tool_definition)
	if frappe.flags.in_migrate:
		installed_tools.append(tool_name)

	return tool_name


def _get_tool_definition(module: ModuleType) -> ToolDefinition:
	"""
	Extract tool definition from a module.

	Args:
		module: Either a Module object or a string path that can be imported
			   (e.g., "otto.tools.kitchen_sink")

	Returns:
		ToolDefinition with extracted attributes from the module
	"""
	from frappe_mcp.server import tools

	if not hasattr(module, "uid") or not isinstance(module.uid, str):
		raise ValueError("Tool definition must have a string named `uid`")

	name = _get_tool_name(module)
	fn = getattr(module, name, None) or getattr(module, "fn", None)
	if fn is None:
		raise ValueError(f"Could not find tool function (with name `{name or 'fn'}`)")

	if not callable(fn):
		raise ValueError(f"Tool function `{name or 'fn'}` is not a callable")

	tool = tools.get_tool(fn)
	annotations = tool["annotations"] or {}
	is_readonly = (
		module.is_readonly if hasattr(module, "is_readonly") else annotations.get("readOnlyHint", False)
	)
	is_destructive = (
		module.is_destructive
		if hasattr(module, "is_destructive")
		else annotations.get("destructiveHint", True)
	)
	is_idempotent = (
		module.is_idempotent if hasattr(module, "is_idempotent") else annotations.get("idempotentHint", False)
	)
	is_open_world = (
		module.is_open_world if hasattr(module, "is_open_world") else annotations.get("openWorldHint", True)
	)
	return ToolDefinition(
		uid=module.uid,
		name=name,
		title=getattr(module, "title", get_title_from_slug(name)),
		description=getattr(module, "description", tool["description"]),
		properties=getattr(module, "properties", tool["input_schema"]["properties"]),
		required=getattr(module, "required", tool["input_schema"]["required"]),
		use_explanation=getattr(module, "use_explanation", False),
		requires_permission=getattr(module, "requires_permission", True),
		dev_mode_only=getattr(module, "dev_mode_only", False),
		output_properties=getattr(module, "output_properties", None),
		output_required=getattr(module, "output_required", None),
		is_readonly=is_readonly if isinstance(is_readonly, bool) else False,
		is_destructive=is_destructive if isinstance(is_destructive, bool) else True,
		is_idempotent=is_idempotent if isinstance(is_idempotent, bool) else False,
		is_open_world=is_open_world if isinstance(is_open_world, bool) else True,
		fn=fn,
	)


def _ensure_tool(tool: ToolDefinition) -> str:
	"""Ensure tool is installed and returns its name"""
	from otto.otto.doctype.otto_tool.otto_tool import OttoTool

	doc: OttoTool
	if not otto.exists("Otto Tool", tool["uid"]):
		doc = OttoTool.new(
			name=tool["uid"],
			title=tool["title"],
			slug=tool["name"],
			description=tool["description"],
			requires_permission=tool["requires_permission"],
			use_explanation=tool["use_explanation"],
			is_app_defined=True,
			tool_import_path=get_import_path(tool["fn"]),
			schema=_get_tool_schema(tool),
			is_readonly=tool["is_readonly"],
			is_destructive=tool["is_destructive"],
			is_idempotent=tool["is_idempotent"],
			is_open_world=tool["is_open_world"],
		)

		assert doc.name is not None, "sanity check"
		return doc.name

	doc = otto.get(OttoTool, tool["uid"])
	doc.title = tool["title"]
	doc.slug = tool["name"]
	doc.description = tool["description"]
	doc.requires_permission = tool["requires_permission"]
	doc.tool_import_path = get_import_path(tool["fn"])
	doc.is_app_defined = True
	doc.is_external = False
	doc.is_valid = True
	doc.reason = None
	doc.code = None
	doc.mock_tool = False
	doc.mock_return_value = None
	doc.use_explanation = tool["use_explanation"]
	doc.is_readonly = tool["is_readonly"]
	doc.is_destructive = tool["is_destructive"]
	doc.is_idempotent = tool["is_idempotent"]
	doc.is_open_world = tool["is_open_world"]
	doc.set_from_schema(_get_tool_schema(tool))
	doc.save(ignore_permissions=True)

	assert doc.name is not None, "sanity check"
	return doc.name


def _get_tool_schema(tool: ToolDefinition) -> ToolSchema:
	return ToolSchema(
		name=tool["name"],
		description=tool["description"],
		parameters=ToolSchemaParameters(
			type="object",
			properties=tool["properties"],
			required=tool["required"],
		),
	)


def _get_tool_name(module: ModuleType) -> str:
	if name := getattr(module, "name", None):
		return name
	name = module.__name__.split(".")[-1]

	if not name.endswith("_tool"):
		raise ValueError(
			f"Could not find tool name. Tool definition file name `{name}` should end with `_tool`"
		)

	return name.split("_tool")[0]
