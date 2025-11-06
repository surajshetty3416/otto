from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

import frappe

import otto
import otto.lib as lib
from otto.assistants.types import AssistantDefinition, AssistantTool
from otto.lib.types import ToolSchema, ToolSchemaParameters
from otto.llm.utils import DEFAULT_INSTRUCTION, DEFAULT_MODEL
from otto.utils import get_import_path

if TYPE_CHECKING:
	from types import ModuleType

__all__ = ["sync_assistants", "sync_otto_assistants"]


def sync_otto_assistants() -> None:
	from otto.assistants import kitchen_sink

	sync_assistants([kitchen_sink])


def sync_assistants(modules: list[ModuleType | str]) -> None:
	for module in modules:
		try:
			assistant = _get_assistant_definition(module)
			_sync_assistant(assistant)
		except Exception:
			otto.log_error(
				title="Error syncing assistant",
				assistant_module=str(module),
			)


def _get_assistant_definition(module: ModuleType | str) -> AssistantDefinition:
	"""
	Extract assistant definition from a module.

	Args:
	    module: Either a Module object or a string path that can be imported
	           (e.g., "otto.assistants.kitchen_sink")

	Returns:
	    AssistantDefinition with extracted attributes from the module
	"""
	# Import module if a string path is provided
	if isinstance(module, str):
		module = import_module(module)

	# Extract required and optional attributes from the module
	return AssistantDefinition(
		uid=module.uid,
		name=module.name,
		dev_mode_only=getattr(module, "dev_mode_only", False),
		instruction=getattr(module, "instruction", DEFAULT_INSTRUCTION),
		tools=getattr(module, "tools", []),
		preferred_model=getattr(module, "preferred_model", DEFAULT_MODEL),
		preferred_config=getattr(module, "preferred_config", None),
		reasoning_effort=getattr(module, "reasoning_effort", None),
		get_context=getattr(module, "get_context", None),
	)


def _sync_assistant(assistant: AssistantDefinition) -> None:
	from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant

	if assistant["dev_mode_only"] and not frappe.conf.developer_mode:
		return

	tools = [_ensure_tools(tool) for tool in assistant["tools"]]
	if not otto.exists("Otto Assistant", assistant["uid"]):
		OttoAssistant.new(
			name=assistant["uid"],
			title=assistant["name"],
			instruction=assistant["instruction"],
			tools=tools,
			llm=_get_model(assistant),
			reasoning_effort=assistant["reasoning_effort"],
			get_context=assistant["get_context"] or None,
			is_app_defined=True,
		)
		return

	doc = otto.get(OttoAssistant, assistant["uid"])
	doc.title = assistant["name"]
	doc.instruction = assistant["instruction"]
	doc.llm = _get_model(assistant)
	doc.reasoning_effort = assistant["reasoning_effort"] or "None"
	doc.is_app_defined = True
	doc.set_get_context(assistant["get_context"])
	doc.set_tools(tools)
	doc.save(ignore_permissions=True)


def _get_model(assistant: AssistantDefinition) -> str:
	config = assistant["preferred_config"] or {}
	return (
		lib.get_model(
			preference=assistant["preferred_model"],
			size=config.get("size"),
			is_reasoning=config.get("is_reasoning"),
			supports_vision=config.get("supports_vision"),
		)
		or DEFAULT_MODEL
	)


def _ensure_tools(tool: AssistantTool) -> str:
	"""Ensure tool is installed and returns its name"""
	from otto.otto.doctype.otto_tool.otto_tool import OttoTool

	doc: OttoTool
	if not otto.exists("Otto Tool", tool["uid"]):
		doc = OttoTool.new(
			name=tool["uid"],
			title=tool["tool"]["title"],
			slug=tool["tool"]["name"],
			description=tool["tool"]["description"],
			requires_permission=tool["requires_permission"],
			use_explanation=tool["use_explanation"],
			is_app_defined=True,
			tool_import_path=get_import_path(tool["tool"]["fn"]),
			schema=_get_tool_schema(tool),
		)

		assert doc.name is not None, "sanity check"
		return doc.name

	doc = otto.get(OttoTool, tool["uid"])
	doc.title = tool["tool"]["title"]
	doc.slug = tool["tool"]["name"]
	doc.description = tool["tool"]["description"]
	doc.requires_permission = tool["requires_permission"]
	doc.tool_import_path = get_import_path(tool["tool"]["fn"])
	doc.is_app_defined = True
	doc.is_external = False
	doc.is_valid = True
	doc.reason = None
	doc.code = None
	doc.mock_tool = False
	doc.mock_return_value = None
	doc.use_explanation = tool["use_explanation"]
	doc.set_from_schema(_get_tool_schema(tool))
	doc.save(ignore_permissions=True)

	assert doc.name is not None, "sanity check"
	return doc.name


def _get_tool_schema(tool: AssistantTool) -> ToolSchema:
	return ToolSchema(
		name=tool["tool"]["name"],
		description=tool["tool"]["description"],
		parameters=ToolSchemaParameters(
			type="object",
			properties=tool["tool"]["input_schema"].get("properties", {}),
			required=tool["tool"]["input_schema"].get("required", []),
		),
	)
