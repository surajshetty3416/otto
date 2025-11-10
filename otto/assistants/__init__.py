from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING

import frappe

import otto
import otto.lib as lib
from otto.assistants.types import AssistantDefinition
from otto.llm.utils import DEFAULT_INSTRUCTION, DEFAULT_MODEL
from otto.utils.imports import import_module

if TYPE_CHECKING:
	from otto.tools.types import ToolDefinition

__all__ = ["sync_assistants", "sync_otto_assistants"]


def sync_assistants(modules: list[ModuleType | str]) -> None:
	for module in modules:
		try:
			sync_assistant(module)
		except Exception as e:
			otto.log_error(
				title="Error syncing assistant",
				assistant_module=str(module),
			)
			if frappe.conf.developer_mode:
				print(e)


def sync_otto_assistants() -> None:
	from otto.assistants import kitchen_sink

	sync_assistants([kitchen_sink])


def sync_assistant(module: ModuleType | str) -> None | str:
	from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant

	# Import module if a string path is provided
	if isinstance(module, str):
		module = import_module(module)

	assistant = _get_assistant_definition(module)

	if assistant["dev_mode_only"] and not frappe.conf.developer_mode:
		return None

	tools_src = assistant["tools"]
	if assistant["get_tools"]:
		tools_src.extend(assistant["get_tools"]())

	tools_ = [_sync_tool(tool) for tool in tools_src]
	tools = [tool for tool in tools_ if tool is not None]
	if not otto.exists("Otto Assistant", assistant["uid"]):
		doc = OttoAssistant.new(
			name=assistant["uid"],
			title=assistant["name"],
			instruction=assistant["instruction"],
			tools=tools,
			llm=_get_model(assistant),
			reasoning_effort=assistant["reasoning_effort"],
			get_context=assistant["get_context"] or None,
			is_app_defined=True,
		)
		return doc.name

	doc = otto.get(OttoAssistant, assistant["uid"])
	doc.title = assistant["name"]
	doc.instruction = assistant["instruction"]
	doc.llm = _get_model(assistant)
	doc.reasoning_effort = assistant["reasoning_effort"] or "None"
	doc.is_app_defined = True
	doc.set_get_context(assistant["get_context"])
	doc.set_tools(tools)
	doc.save(ignore_permissions=True)

	assert doc.name is not None, "sanity check"
	return doc.name


def _get_assistant_definition(module: ModuleType) -> AssistantDefinition:
	"""
	Extract assistant definition from a module.

	Args:
	    module: Either a Module object or a string path that can be imported
	           (e.g., "otto.assistants.kitchen_sink")

	Returns:
	    AssistantDefinition with extracted attributes from the module
	"""

	# Extract required and optional attributes from the module
	return AssistantDefinition(
		uid=module.uid,
		name=module.name,
		dev_mode_only=getattr(module, "dev_mode_only", False),
		instruction=getattr(module, "instruction", DEFAULT_INSTRUCTION),
		tools=getattr(module, "tools", []),
		get_tools=getattr(module, "get_tools", None),
		preferred_model=getattr(module, "preferred_model", DEFAULT_MODEL),
		preferred_config=getattr(module, "preferred_config", None),
		reasoning_effort=getattr(module, "reasoning_effort", None),
		get_context=getattr(module, "get_context", None),
	)


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


def _sync_tool(tool: ToolDefinition | ModuleType | str) -> str | None:
	"""Ensure tool is installed and returns its name"""

	if isinstance(tool, (str | ModuleType)):
		from otto.tools import sync_tool

		return sync_tool(tool)
	from otto.tools import _ensure_tool

	if tool["dev_mode_only"] and not frappe.conf.developer_mode:
		return None

	return _ensure_tool(tool)
