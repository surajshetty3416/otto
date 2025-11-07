from __future__ import annotations

from typing import TYPE_CHECKING

from frappe_mcp.server import tools

from otto.tools.types import ToolDefinition

if TYPE_CHECKING:
	from collections.abc import Callable

	from frappe_mcp.server.tools import ToolOptions


def get_tool(
	fn: Callable,
	uid: str,
	title: str | None = None,
	*,
	requires_permission: bool = False,
	use_explanation: bool = False,
	options: ToolOptions | None = None,
	dev_mode_only: bool = False,
) -> ToolDefinition:
	from frappe_mcp.server.tools import ToolOptions

	from otto.utils import get_title_from_slug

	options = options or ToolOptions()
	options["title"] = title or get_title_from_slug(fn.__name__)
	tool = tools.get_tool(fn, options)
	title = title or tool["title"] or get_title_from_slug(tool["name"])
	output_schema = tool.get("output_schema", {}) or {}
	annotations = options.get("annotations") or None

	return ToolDefinition(
		uid=uid,
		name=tool["name"],
		title=title,
		description=tool["description"],
		properties=tool["input_schema"].get("properties", {}),
		required=tool["input_schema"].get("required", []),
		requires_permission=requires_permission,
		use_explanation=use_explanation,
		dev_mode_only=dev_mode_only,
		output_properties=output_schema.get("properties", None),
		output_required=output_schema.get("required", None),
		annotations=annotations,
		fn=fn,
	)
