from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
	from collections.abc import Callable


class ToolDefinition(TypedDict):
	"""
	Describes the schema for an Otto Tool. Used to construct or update Otto Tool entries and to expose tools for assistants and LLMs.

	Attributes:
		uid: Unique identifier for the Otto Tool entry (used as the record key).
		name: Internal and LLM-facing name for the tool (should also match the tool function name).
		title: Human-readable name of the tool (defaults to capitalized `name` if not provided).
		description: Tool summary for user-facing and LLM context (usually from the function docstring).
		properties: Arguments schema for tool inputs, as a dict mapping argument names to schemas.
		required: List of required parameters for the tool function.
		use_explanation: If True, the tool will prompt the LLM to provide an explanation/rationale when invoking the tool.
		requires_permission: If True, invoking the tool may require elevated permissions or user consent.
		dev_mode_only: If True, tool is only available in developer mode.
		output_properties: Optional schema describing the output structure of the tool.
		output_required: Optional list describing required fields in the output.
		is_readonly: If True, the tool does not modify its environment (default is False).
		is_destructive: If True, the tool may perform destructive updates to its environment (default is True).
		is_idempotent: If True, calling the tool repeatedly with the same arguments will have no additional effect on the its environment (default is False).
		is_open_world: If True, the tool may interact with an "open world" of external entities (default is True).
		fn: The Python callable implementing the tool logic.

	Notes:
	- The file name for a tool should be `{name}_tool.py` this is used to infer `name` if not provided.
	- The function providing the tool implementation should match `name` or be referenced as `fn`.
	- If `required` is not provided, it will be inferred from type annotations if given.
	- If `properties` are not provided, it will be inferred from type annotations and the docstring if given.
	- If `title` is not provided, capital-cased version of `name` is used.
	- If `name` is not provided, it will be inferred from the file name.
	- If `fn` is not provided, then tool function will be inferred from the value of `name`.
	- If `description` is not provided, it will be inferred from the docstring of the tool function.
	- Title and description can be inferred if omitted.
	- In case of complex tool properties, it is recommended to explicitly define them.
	"""

	uid: str
	name: str
	title: str
	description: str
	properties: dict[str, Any]
	required: list[str]
	use_explanation: bool
	requires_permission: bool
	dev_mode_only: bool
	fn: Callable

	"""
	Additional attributes defined by the ModelContextProtocol Tool schema,
	mentioned here for completeness. These aren't currently used by Otto but may
	be in the future.
	"""
	# ref: https://modelcontextprotocol.io/specification/2025-06-18/schema#tool
	output_properties: dict[str, Any] | None
	output_required: list[str] | None

	# Annotation flags from ModelContextProtocol ToolAnnotations
	# ref: https://modelcontextprotocol.io/specification/2025-06-18/schema#toolannotations
	is_readonly: bool = False
	is_destructive: bool = True
	is_idempotent: bool = False
	is_open_world: bool = True
