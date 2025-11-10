from __future__ import annotations

from typing import TYPE_CHECKING, Any

from frappe_mcp.server import tools

from otto.tools.types import ToolDefinition

if TYPE_CHECKING:
	from collections.abc import Callable


def get_tool(
	fn: Callable,
	uid: str,
	title: str | None = None,
	*,
	# Flags
	requires_permission: bool = True,
	use_explanation: bool = False,
	dev_mode_only: bool = False,
	use_entire_docstring: bool = False,
	# Metadata
	name: str | None = None,
	description: str | None = None,
	properties: dict[str, Any] | None = None,
	required: list[str] | None = None,
	# Annotations Flags
	is_readonly: bool = False,
	is_destructive: bool = True,
	is_idempotent: bool = False,
	is_open_world: bool = True,
	# Output
	output_properties: dict[str, Any] | None = None,
	output_required: list[str] | None = None,
) -> ToolDefinition:
	from frappe_mcp.server.tools import ToolOptions

	from otto.utils import get_title_from_slug

	tool = tools.get_tool(fn, ToolOptions(use_entire_docstring=use_entire_docstring))
	name = name or tool["name"]
	output_schema = tool.get("output_schema", {}) or {}

	return ToolDefinition(
		uid=uid,
		name=name,
		# Metadata
		title=title or get_title_from_slug(name),
		description=description or tool["description"],
		properties=properties or tool["input_schema"].get("properties", {}),
		required=required or tool["input_schema"].get("required", []),
		# Flags
		requires_permission=requires_permission,
		use_explanation=use_explanation,
		dev_mode_only=dev_mode_only,
		# Output
		output_properties=output_properties or output_schema.get("properties", None),
		output_required=output_required or output_schema.get("required", None),
		# Annotation flags
		is_readonly=is_readonly,
		is_destructive=is_destructive,
		is_idempotent=is_idempotent,
		is_open_world=is_open_world,
		fn=fn,
	)
