from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from otto.assistants.types import AssistantDefinition
from otto.llm.utils import DEFAULT_INSTRUCTION, DEFAULT_MODEL

if TYPE_CHECKING:
	from types import ModuleType


def get_assistant_definition(module: ModuleType | str) -> AssistantDefinition:
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


def install_assistant(assistant: AssistantDefinition) -> None:
	return None
