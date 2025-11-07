from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
	from collections.abc import Callable
	from types import ModuleType

	from otto.lib.types import ModelSize, ReasoningEffort
	from otto.tools.types import ToolDefinition

	ToolList = list[ToolDefinition | ModuleType | str]


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
		get_context: Function with signature: <code>def get_context() -> dict[str, str]</code> used to template the instruction.
		tools: List of ToolDefinition objects. Default is empty list.
			items in the tool list can also be
			- a dot separated module path to a tool module "path.to.tool.name_tool" (i.e. the module containing the tool)
			- a tool module object, i.e. an imported tool module
			in both of the above cases the tool should follow the ToolDefinition file format defined in `otto.tools.types.ToolDefinition`
		get_tools: Function with signature: `def get_tools() -> ToolList` used to dynamically load tools. Default is None.
			- if provided, it will be used along with the `tools` list to load tools.
	"""

	uid: str
	name: str
	dev_mode_only: bool
	instruction: str
	tools: ToolList
	get_tools: Callable[[], ToolList] | None
	preferred_model: str | None
	preferred_config: ModelPreferenceConfig | None
	reasoning_effort: ReasoningEffort | None
	get_context: Callable[[], dict[str, str]] | None


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
