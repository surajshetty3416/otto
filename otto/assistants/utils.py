from __future__ import annotations

from typing import TYPE_CHECKING

from frappe_mcp.server import tools

if TYPE_CHECKING:
	from collections.abc import Callable

	from frappe_mcp.server.tools import ToolOptions

	from otto.assistants.types import AssistantTool


def get_tool(
	fn: Callable,
	uid: str,
	title: str | None = None,
	*,
	requires_permission: bool = False,
	use_explanation: bool = False,
	options: ToolOptions | None = None,
) -> AssistantTool:
	from frappe_mcp.server.tools import ToolOptions

	from otto.assistants.types import AssistantTool
	from otto.utils import get_title_from_slug

	options = options or ToolOptions()
	options["title"] = title or get_title_from_slug(fn.__name__)

	return AssistantTool(
		uid=uid,
		tool=tools.get_tool(fn, options),
		requires_permission=requires_permission,
		use_explanation=use_explanation,
	)
