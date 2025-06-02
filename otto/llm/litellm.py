"""
This file encapsulates the interaction with LiteLLM.  No LiteLLM specific code
should exist outside this file.

The `interact` function is the main function to interact with the LLM. If
deprecating the use of LiteLLM, just the interact function in this file needs to
be implemented.

LiteLLM is being used as a means of convenience so as to allow not having to
deal with multiple providers individually. While this convenience is
appreciated, LiteLLM's code and docs quality, at the time of writing, are not up
to the mark.
"""

# TODO:
# - handle refusals
# - handle error outs

from __future__ import annotations

import json
import os
import threading
import time
from typing import TYPE_CHECKING

import frappe.realtime

import otto
from otto.llm.format import get_messages
from otto.llm.types import (
	Content,
	ContentChunk,
	Exchange,
	ExchangeItem,
	InteractResponse,
	TextContent,
	ThinkingContent,
	ThinkingEffort,
	ToolUseContent,
	UserContent,
)
from otto.llm.utils import (
	get_agent_item,
	get_exchange,
	get_exchange_list,
	to_content,
	update_exchange,
)

if TYPE_CHECKING:
	from datetime import datetime

	from litellm import CustomStreamWrapper
	from litellm.types.utils import ModelResponseStream


DEFAULT_LLM = "openai/gpt-4.1-mini"
MAX_RETRIES = 3

logger = otto.logger("otto_litellm")
thinking_budget_map: dict[ThinkingEffort, int] = {
	"low": 8000,
	"medium": 16000,
	"high": 32000,
}


def interact(
	# query should be None only if exchange is provided with a call call update
	query: str | list[str | UserContent] | list[UserContent] | None = None,
	*,
	exchange: Exchange | None = None,
	model: str | None = None,
	exchange_id: str | None = None,
	system: str | None = None,
	tools: list[dict] | None = None,
	thinking_effort: ThinkingEffort | None = None,
) -> tuple[InteractResponse, None] | tuple[None, str]:
	"""
	Interacts with an LLM using LiteLLM, handling conversation history,
	streaming responses, and tool usage.

	Maintaining state:

	1. The `interact` function maintains state using an Exchange object. If no exchange
		object is provided, a new one is created.
	2. The provided exchange object should not contain the query. An item for the query is
		created and added to the exchange object.
	3. The `interact` function returns an updated exchange object on success.
	4. The returned exchange object will contain the user query and the agent response.
	5. To maintain history the returned object should be provided to the `interact` function
		upon each call.
	6. The returned Exchange object may be updated in the case of certain
		instances, such as if appending a tool use response.

	Args:
		query: The user's input query to start a new conversation or continue an
			existing one.
		exchange: The existing conversation history (Exchange object) WITHOUT the query.
			Users query is added to the Exchange and an updated Exchange is returned.
			Required if `query` is not provided.
		model: The specific LiteLLM model identifier (e.g., "openai/gpt-4o").
			Overrides `model` if provided. If neither is provided, derived from `DEFAULT_LLM`.
		exchange_id: An optional identifier for the exchange, potentially used for
			real-time updates.
		system: An optional system prompt to guide the LLM's behavior.
		tools: An optional list of tools (functions) the LLM can use.

	Returns:
		- On success: A tuple `(InteractResponse, None)`, where `InteractResponse`
			contains the generated agent response item, the updated exchange, and
			a list of content chunks from the stream.
		- On failure (e.g., API key issue): A tuple `(None, str)` containing
			`None` and an error reason string.
	"""
	import litellm

	assert query is not None or exchange is not None, (
		"exchange (with tool result) is required if query is not provided"
	)

	content = None if query is None else to_content(query)
	model = model or DEFAULT_LLM

	# Creates a new exchange if exchange is None, else uses a copy
	update = get_exchange(content, exchange)

	if reason := _set_key(model):
		return None, reason

	item = get_agent_item(model)
	item["meta"]["start_time"] = time.time()

	# Required cause of LiteLLM's spaghetti design
	done = threading.Event()
	done.clear()

	def success_callback(
		kwargs: dict,  # kwargs to completion
		completion_response: dict,  # response from completion
		_start_time: datetime,
		_end_time: datetime,
	):
		usage = completion_response.get("usage", {})
		logger.debug(
			{
				"message": "callback called",
				"id": item["id"],
				"usage": usage.get("completion_tokens"),
				"end_reason": completion_response.get("choices", [{}])[0].get("finish_reason"),
			}
		)
		if usage.get("completion_tokens") is None or usage.get("prompt_tokens") is None:
			return  # Test based heuristic on when callback is final

		if (end_reason := _get_end_reason(completion_response)) is None:
			return  # Success callback is called multiple times for each chunk

		item["meta"]["input_tokens"] = usage.get("prompt_tokens", 0)
		item["meta"]["output_tokens"] = usage.get("completion_tokens", 0)
		item["meta"]["cost"] = kwargs.get("standard_logging_object", {}).get("response_cost", None)
		item["content"] = _get_content(completion_response)
		item["meta"]["end_reason"] = end_reason
		logger.debug({"message": "callback done set", "id": item["id"]})
		done.set()

	litellm.success_callback = [success_callback]

	items = get_exchange_list(update)
	messages, last_id = get_messages(
		items,
		system,
		preserve_thinking=_should_preserve_thinking(model),
	)

	think = {}
	if thinking_effort:
		think["reasoning_effort"] = thinking_effort
		think["thinking"] = _get_thinking(thinking_effort)

	logger.debug({"message": "calling litellm.completion", "id": item["id"]})
	completion = completions(
		model=model,
		messages=messages,
		tools=tools,
		stream=True,
		**think,
		# Drops incompatible params (doesn't seem to always work)
		drop_params=True,
	)

	# litellm.completion not typed well enough; this shouldn't throw when stream=True
	assert isinstance(completion, litellm.CustomStreamWrapper), "sanity check"

	# Iterates over the completion stream and returns a list of ContentChunk
	chunks, signature = _stream(completion, item, exchange_id)

	logger.debug({"message": "waiting for callback", "id": item["id"]})
	# Wait until the success callback is called
	done.wait()

	# Rest of the item updation is handled in litellm.success_callback
	# Thinking signature is required by anthropic
	if signature:
		for c in item["content"]:
			if c["type"] == "thinking":
				c["signature"] = signature

	logger.debug({"message": "updating exchange", "id": item["id"]})
	# Update the update exchange with the item
	update_exchange(update, last_id, item)

	item["meta"]["end_time"] = time.time()

	return InteractResponse(item=item, update=update, chunks=chunks), None


def _get_content(completion_response: dict):
	content: list[Content] = []
	comp = completion_response.get("choices", [])[0]
	message = comp.get("message", {})

	if message.get("reasoning_content"):
		content.append(
			ThinkingContent(
				type="thinking",
				text=message.get("reasoning_content"),
				signature=None,
			)
		)

	if message.get("content"):
		content.append(
			TextContent(
				type="text",
				text=message.get("content"),
			)
		)

	if message.get("tool_calls"):
		for tool_call in message.get("tool_calls", []):
			func = tool_call.get("function")
			content.append(
				ToolUseContent(
					type="tool_use",
					id=tool_call.get("id"),
					name=func.get("name"),
					args=json.loads(func.get("arguments")),
					status="pending",
					result=None,
				)
			)

	return content


def completions(**kwargs):
	"""Wrapper around litellm.completion that retries on rate limit errors."""
	retries = 0
	import litellm

	while True:
		try:
			return litellm.completion(**kwargs)
		except litellm.RateLimitError as e: # type: ignore
			otto.log_error("LiteLLM Completion Error", model=kwargs.get("model"))
			if retries >= MAX_RETRIES or "request would exceed the rate limit" not in str(e):
				raise e

			retries += 1

			# Anthropic rate limit is set on a per minute basis
			time.sleep(61)


def _stream(completion: CustomStreamWrapper, item: ExchangeItem, exchange_id: str | None):
	"""
	Iterates over the completion stream iterable, publishes the chunks, collates
	them into a list and if a signature is found, updates the item's content.

	returns a list of ContentChunk
	"""
	signature = None
	chunks: list[ContentChunk] = []

	for chunk in completion:
		if cc := _stream_chunk(chunk, item["id"], exchange_id):
			logger.debug({"id": item["id"], "content": cc["content"]})
			chunks.append(cc)

		signature = _get_signature(chunk)
	return chunks, signature


def _stream_chunk(chunk: ModelResponseStream, item_id: str, exchange_id: str | None):
	"""
	publish using user, exchange_id, item_id
	"""
	delta = chunk.choices[0].delta
	cc = ContentChunk(
		type="text",
		content="",
		item_id=item_id,
		exchange_id=exchange_id or "",
	)

	if hasattr(delta, "reasoning_content") and delta.reasoning_content:
		cc["type"] = "thinking"
		cc["content"] = delta.reasoning_content

	elif hasattr(delta, "content") and delta.content:
		cc["type"] = "text"
		cc["content"] = delta.content

	elif (
		hasattr(delta, "tool_calls")
		and delta.tool_calls
		and (name := delta.tool_calls[0].function.get("name"))
	):
		cc["type"] = "tool_use"
		cc["content"] = name

	else:
		return None

	if exchange_id and frappe.session.user:
		frappe.realtime.publish_realtime(
			event="otto_interaction",
			user=frappe.session.user,
			message={"type": "content_chunk", "data": cc},
		)

	return cc


def _get_end_reason(completion_response: dict):
	comp = completion_response.get("choices", [{}])[0]
	if comp.get("finish_reason") == "tool_use" or comp.get("finish_reason") == "tool_calls":
		return "tool_use"

	if comp.get("finish_reason") == "stop":
		return "turn_end"

	return None


def _set_key(model: str) -> str | None:
	from frappe.utils.password import get_decrypted_password

	if model.startswith("openai"):
		key = "OPENAI_API_KEY"
	elif model.startswith("anthropic"):
		key = "ANTHROPIC_API_KEY"
	else:
		return None

	value = get_decrypted_password("Otto Settings", "Otto Settings", key.lower())
	if not value:
		return f"API key {key.lower()} not set"

	os.environ[key] = value
	return None


def _get_signature(chunk: ModelResponseStream):
	"""
	Signature is not passed in the completions object and needs to be extracted
	from the stream chunk.
	"""
	if not (delta := (chunk.choices or [{}])[0].get("delta", {})):
		return None

	if not (thinking_blocks := delta.get("thinking_blocks", [])):
		return None

	return thinking_blocks[0].get("signature") or None


def _should_preserve_thinking(model: str):
	# rn only Sonnet 3.7 requires reasoning to be preserved
	# reference: https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking?q=thinking#preserving-thinking-blocks
	return "sonnet" in model


def _get_thinking(thinking_effort: ThinkingEffort | None):
	if thinking_effort is None:
		return None

	return {"type": "enabled", "budget_tokens": thinking_budget_map[thinking_effort]}
