from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from otto.llm.types import SessionItem


class C:
	"""
	Return dict formatted content for OpenAI Chat Completion.

	reference: https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages
	"""

	@staticmethod
	def text(text: str):
		return {"type": "text", "text": text}

	@staticmethod
	def image(url: str):
		return {"type": "image_url", "image_url": {"url": url}}

	@staticmethod
	def file(name: str, data: str):
		return {
			"type": "file",
			"file": {"filename": name, "file_data": data},
		}

	@staticmethod
	def tool_use(id: str, name: str, args: dict):
		return {
			"type": "function",
			"id": id,
			"function": {"name": name, "arguments": json.dumps(args)},
		}

	@staticmethod
	def tool_response(id: str, result: str):
		return {
			"role": "tool",
			"tool_call_id": id,
			"content": str(result),
		}

	@staticmethod
	def thinking(text: str, signature: str | None):
		# LiteLLM specific, used only by Anthropic, OpenAI throws error
		thinking = {
			"type": "thinking",
			"thinking": text,
		}

		if signature:
			thinking["signature"] = signature

		return thinking


def get_messages(
	items: list[SessionItem],
	system: str | None = None,
	preserve_thinking: bool = False,
):
	"""
		Converts from Otto internal format, i.e. SessionItem, to OpenAI Chat
	Completion format. LiteLLM makes use of OpenAI Chat Completion format.

	Reference: https://platform.openai.com/docs/api-reference/chat/create
	"""
	messages = []
	last_id = None

	if system:
		messages.append({"role": "system", "content": system})

	for item in items:
		last_id = item["id"]
		message: dict = {"role": _get_role(item)}

		content, tool_calls, tool_responses = _get_content(item, preserve_thinking)
		if content:
			message["content"] = content

		if tool_calls:
			message["tool_calls"] = tool_calls

		messages.append(message)

		# Tool responses are added as separate messages with role "tool"
		for res in tool_responses:
			messages.append(res)

	assert last_id is not None, "sanity check"
	return messages, last_id


def _get_content(item: SessionItem, preserve_thinking: bool):
	content: str | list[dict] = []
	tool_calls: list[dict] = []
	tool_responses: list[dict] = []

	for part in item["content"]:
		if part["type"] == "text":
			c = C.text(part["text"])
			content.append(c)
			continue

		if part["type"] == "image":
			url = part["url"] or part["data"]
			assert url is not None, "sanity check"

			c = C.image(url)
			content.append(c)
			continue

		if part["type"] == "file":
			c = C.file(part["name"], part["data"])
			content.append(c)
			continue

		if part["type"] == "thinking":
			if not preserve_thinking:
				continue

			c = C.thinking(part["text"], part["signature"])
			content.append(c)
			continue

		assert part["type"] == "tool_use"
		c = C.tool_use(part["id"], part["name"], part["args"])
		tool_calls.append(c)

		if part["status"] != "pending":
			assert part["result"] is not None, "sanity check"
			c = C.tool_response(part["id"], part["result"])
			tool_responses.append(c)

	if len(content) == 1 and content[0]["type"] == "text":
		content = content[0]["text"]

	return content, tool_calls, tool_responses


def _get_role(item: SessionItem):
	if item["meta"]["role"] == "user":
		return "user"

	if item["meta"]["role"] == "agent":
		return "assistant"

	raise AssertionError("no-op")
