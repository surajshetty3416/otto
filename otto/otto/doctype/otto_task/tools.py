from __future__ import annotations

from otto.llm.types import Content

"""
Definitions for meta tools to be used by Otto to perform some task.

Meta tools don't execute any code but might affect the control flow of task
execution or will assist the LLM in performing the task.
"""

think_tool = {
	# https://www.anthropic.com/engineering/claude-think-tool
	"type": "function",
	"function": {
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
	},
}

end_task_tool = {
	"type": "function",
	"function": {
		"name": "end_task",
		"description": "Use this tool to indicate the completion of this task. It should be called only once after the task has completed.",
		"parameters": {
			"type": "object",
			"properties": {
				"explanation": {
					"type": "string",
					"description": "Short explanation of why the task is being marked as completed.",
				}
			},
			"required": ["explanation"],
		},
	},
}

meta_tools = [think_tool, end_task_tool]


def is_meta_tool(tool: Content) -> bool:
	if tool["type"] != "tool_use":
		return False

	return tool["name"] in [t["function"]["name"] for t in meta_tools]


def has_task_ended(tool: Content) -> bool:
	return tool["type"] == "tool_use" and tool["name"] == "end_task"
