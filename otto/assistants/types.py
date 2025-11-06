from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
	from collections.abc import Callable

	from frappe_mcp import Tool

	from otto.lib.types import ModelSize, ReasoningEffort


class AssistantDefinition(TypedDict):
	"""
	An assistant folder should have a __init__.py file where the following
	variables should be defined (see `./kitchen_sink/__init__.py` for an
	example).

	The variables will be extracted to form an AssistantDefinition object. This
	object will then be used to create an Otto Assistant entry or update an
	existing one if it's found (matching `name`).

	Attributes:
		name: Unique internal identifier for the assistant (name of the Otto Assistant). Required.
		title: Human-readable title of the assistant. Required.
		dev_mode_only: If True, assistant is installed only in dev mode. Default is False.
		preferred_model: ID (substring) of the preferred model for this assistant. Default is DEFAULT_MODEL.
		preferred_config: Preferred model configuration, see ModelPreferenceConfig. Default is DEFAULT_MODEL.
		reasoning_effort: Default level of reasoning effort (see ReasoningEffort). Default is "None".
		instruction: System prompt or instruction to guide the assistant, supports Jinja template for adding context. Default is DEFAULT_INSTRUCTION.
		tools: List of Tool objects the assistant can use use (frappe_mcp.get_tool for convenience). Default is empty list.
		get_context: Function with signature: <code>def get_context() -> dict[str, str]</code> used to template the instruction.
	"""

	uid: str
	name: str
	dev_mode_only: bool
	instruction: str
	tools: list[AssistantTool]
	preferred_model: str | None
	preferred_config: ModelPreferenceConfig | None
	reasoning_effort: ReasoningEffort | None
	get_context: Callable[[], dict[str, str]] | None


class AssistantTool(TypedDict):
	uid: str
	tool: Tool
	requires_permission: bool


class ModelPreferenceConfig(TypedDict, total=False):
	"""
	Model preference configuration for an assistant; documentation for each field.

	Attributes:
		size: The preferred model size (see ModelSize).
		is_reasoning: True if the model is reasoning-capable.
		supports_vision: True if the model supports visual input.
	"""

	size: ModelSize
	is_reasoning: bool
	supports_vision: bool
