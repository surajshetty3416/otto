from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from otto.llm.types import Content, ToolSchema

"""
Definitions for meta tools to be used by Otto to perform some task.

Meta tools don't execute any code but might affect the control flow of task
session or will assist the LLM in performing the task.
"""

think_tool: ToolSchema = {
	# https://www.anthropic.com/engineering/claude-think-tool
	"name": "think",
	"description": "Use this tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.",
	"parameters": {
		"type": "object",
		"properties": {
			"thought": {
				"type": "string",
				"description": "A thought to think about",
			},
		},
		"required": ["thought"],
	},
}

end_task_tool: ToolSchema = {
	"name": "end_task",
	"description": "Use this tool to indicate the success or failure of this task. It should be called only once.",
	"parameters": {
		"type": "object",
		"properties": {
			"explanation": {
				"type": "string",
				"description": "Short explanation of why the task is being ended.",
			}
		},
		"required": ["explanation"],
	},
}

meta_tools: list[ToolSchema] = [think_tool, end_task_tool]


def is_meta_tool(tool: Content | str) -> bool:
	if isinstance(tool, str):
		return tool in [t["name"] for t in meta_tools]

	if tool["type"] != "tool_use":
		return False

	return tool["name"] in [t["name"] for t in meta_tools]
