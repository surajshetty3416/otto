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
	options: ToolOptions | None = None,
) -> AssistantTool:
	from otto.assistants.types import AssistantTool

	if options and title:
		options["title"] = title

	return AssistantTool(
		uid=uid,
		tool=tools.get_tool(fn, options),
		requires_permission=requires_permission,
	)
