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

from __future__ import annotations

import json
import os
import random
import threading
import time
from typing import TYPE_CHECKING, Any, NamedTuple, cast

import otto
from otto.llm.format import get_messages
from otto.llm.types import (
	Content,
	ContentChunk,
	InteractReturn,
	Query,
	ReasoningEffort,
	Session,
	SessionItem,
	TextContent,
	ThinkingContent,
	ToolUseContent,
)
from otto.llm.utils import (
	DEFAULT_MODEL,
	DEFAULT_REASONING_BUDGET_MAP,
	MAX_RETRIES,
	get_agent_item,
	get_key,
	get_provider,
	get_sequence,
	get_session,
	to_content,
	update_session,
)

if TYPE_CHECKING:
	from collections.abc import Generator
	from datetime import datetime

	from litellm import CustomStreamWrapper
	from litellm.types.utils import ModelResponseStream


logger = otto.logger("otto.llm.litellm", "ERROR")


class StreamReturn(NamedTuple):
	chunks: list[ContentChunk]
	latency: float


class InteractReturnTuple(NamedTuple):
	response: InteractReturn | None
	reason: None | str


def interact(
	# query should be None only if session is provided with a call call update
	query: Query | None = None,
	*,
	session: Session | None = None,
	model: str | None = None,
	system: str | None = None,
	tools: list[dict] | None = None,
	reasoning_effort: ReasoningEffort | None = None,
) -> Generator[ContentChunk, None, InteractReturnTuple]:
	"""
	Interacts with an LLM using LiteLLM, handling conversation history,
	streaming responses, and tool usage.

	This function is a generator that yields response chunks and returns a final
	named tuple with the complete interaction response.

	Maintaining state:

	1. The `interact` function maintains state using a `Session` object. If no session
		object is provided, a new one is created.
	2. The provided session object should not contain the query. An item for the query is
		created and added to the session object.
	3. The `interact` generator's return value contains an updated session object on success.
	4. The returned session object will contain the user query and the agent response.
	5. To maintain history the returned object should be provided to the `interact` function
		upon each call.
	6. The returned `Session` object may be updated in certain cases, such
		as if appending a tool use response.

	Args:
		query: The user's input query to start a new conversation or continue an
			existing one.
		session: The existing conversation history (Session object) WITHOUT the query.
			Users query is added to the Session and an updated Session is returned.
			Required if `query` is not provided.
		model: The specific LiteLLM model identifier (e.g., "openai/gpt-4o").
			Overrides `model` if provided. If neither is provided, derived from `DEFAULT_LLM`.
		system: An optional system prompt to guide the LLM's behavior.
		tools: An optional list of tools (functions) the LLM can use.
		reasoning_effort: An optional reasoning effort to use if the model supports it.

	Yields:
		ContentChunk: Chunks of the response from the LLM as they are generated.

	Returns:
		InteractReturnTuple:
			- On success, `InteractReturnTuple.response` contains an `InteractReturn`
			  object with the generated agent response item, the updated session,
			  and a list of content chunks from the stream. `InteractReturnTuple.reason` is `None`.
			- On failure (e.g., API key issue), `InteractReturnTuple.response` is `None` and
			  and `InteractReturnTuple.reason` contains reason for failure.
	"""
	import litellm

	assert query is not None or session is not None, (
		"session (with tool result) is required if query is not provided"
	)

	content = None if query is None else to_content(query)
	model = model or DEFAULT_MODEL

	# Creates a new session if session is None, else uses a copy
	update = get_session(content, session)
	session_id = update["id"]

	if reason := _set_key(model):
		return InteractReturnTuple(None, reason)

	item = get_agent_item(model)
	item["meta"]["start_time"] = time.time()

	# Required cause of LiteLLM's spaghetti design
	done = threading.Event()

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

	items = get_sequence(update)
	messages, last_id = get_messages(
		items,
		system,
		preserve_thinking=_should_preserve_thinking(model),
	)

	think = {}
	if reasoning_effort:
		think["reasoning_effort"] = reasoning_effort.lower()  # litellm expects "low", "medium", "high"

	if reasoning_effort and (model.startswith("anthropic") or model.startswith("gemini")):
		think["thinking"] = _get_thinking(reasoning_effort)

	logger.debug({"message": "calling litellm.completion", "id": item["id"]})
	completion = _completions(
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

	chunks = []

	# Iterates over the completion stream and returns a list of ContentChunk
	stream_generator = _stream(completion, item, session_id)
	while True:
		try:
			yield next(stream_generator)
			if item["meta"]["time_to_first_chunk"] == 0:
				item["meta"]["time_to_first_chunk"] = time.time() - item["meta"]["start_time"]
		except StopIteration as e:
			ret = cast("StreamReturn", e.value)
			chunks = ret.chunks
			item["meta"]["inter_chunk_latency"] = ret.latency
			break

	logger.debug(
		{
			"message": "stream completed",
			"id": item["id"],
			"chunks": len(chunks),
		}
	)
	done.wait()

	logger.debug(
		{
			"message": "success callback called",
			"content_len": len(item["content"]),
			"thinking_content": [c for c in item["content"] if c["type"] == "thinking"],
		}
	)

	logger.debug({"message": "updating session", "id": item["id"]})
	# Update the update session with the item
	update_session(update, last_id, item)

	item["meta"]["end_time"] = time.time()

	response = InteractReturn(item=item, update=update, chunks=chunks)
	return InteractReturnTuple(response, None)


def _get_content(completion_response: dict) -> list[Content]:
	message = completion_response.get("choices", [{}])[0].get("message", {})
	return [
		*_get_thinking_content(message),
		*_get_text_content(message),
		*_get_tool_use_content(message),
	]


def _get_thinking_content(message: dict[str, Any]) -> list[ThinkingContent]:
	thinking_blocks = message.get("thinking_blocks") or []
	reasoning_content = message.get("reasoning_content")

	if not (thinking_blocks or reasoning_content):
		return []

	if reasoning_content and not thinking_blocks:
		assert isinstance(reasoning_content, str), "sanity check"
		return [
			ThinkingContent(
				type="thinking",
				text=reasoning_content,
				signature=None,
			)
		]

	# Thinking blocks are set by litellm only when model is an anthropic one we
	# don't directly use reasoning_content cause anthropic sends signatures with
	# thinking which needs to be sent back in the next request.
	blocks: list[ThinkingContent] = []
	for block in thinking_blocks:
		text = block.get("thinking")
		if not text:
			continue

		blocks.append(
			ThinkingContent(
				type="thinking",
				text=text,
				signature=block.get("signature"),
			)
		)

	return blocks


def _get_text_content(message: dict[str, Any]) -> list[TextContent]:
	if text := message.get("content"):
		return [TextContent(type="text", text=text)]

	return []


def _get_tool_use_content(message: dict[str, Any]) -> list[ToolUseContent]:
	content: list[ToolUseContent] = []
	if not message.get("tool_calls"):
		return content

	for tool_call in message.get("tool_calls", []):
		func = tool_call.get("function")
		content.append(
			ToolUseContent(
				type="tool_use",
				id=tool_call.get("id"),
				name=func.get("name"),
				args=json.loads(func.get("arguments")),
				override=None,
				status="pending",
				result=None,
				start_time=0,
				end_time=0,
				stdout=None,
				stderr=None,
			)
		)
	return content


def _completions(**kwargs):
	"""Wrapper around litellm.completion that retries on rate limit errors."""
	retries = 0
	import litellm

	while True:
		try:
			return litellm.completion(**kwargs)
		except Exception as e:  # type: ignore
			if retries >= MAX_RETRIES or (
				"request would exceed the rate limit" not in str(e) and "Overloaded" not in str(e)
			):
				e.add_note("number of retries: " + str(retries))
				otto.log_error("litellm_completion error", model=kwargs.get("model"))
				raise e

			# Anthropic rate limit is set on a per minute basis
			delay = min(random.randint(0, 5 * (2**retries)), 60)
			time.sleep(delay)

			retries += 1


def _stream(
	completion: CustomStreamWrapper, item: SessionItem, session_id: str | None
) -> Generator[ContentChunk, None, StreamReturn]:
	"""
	Iterates over the completion stream iterable, publishes the chunks, collates
	them into a list and if a signature is found, updates the item's content.

	returns a list of ContentChunk
	"""
	timestamps: list[float] = []
	chunks: list[ContentChunk] = []

	yield ContentChunk(
		type="system",
		message="start",
		content="",
		item_id=item["id"],
		session_id=session_id or "",
	)

	try:
		for chunk in completion:
			timestamps.append(time.time())
			if cc := _stream_chunk(chunk, item["id"], session_id):
				logger.debug({"id": item["id"], "content": cc["content"]})
				chunks.append(cc)
				yield cc
	except Exception as e:
		yield ContentChunk(
			type="system",
			message="error",
			content=str(e),
			item_id=item["id"],
			session_id=session_id or "",
		)
		raise e

	yield ContentChunk(
		type="system",
		message="end",
		content="",
		item_id=item["id"],
		session_id=session_id or "",
	)

	return StreamReturn(chunks, _get_inter_chunk_latency(timestamps))


def _stream_chunk(chunk: ModelResponseStream, item_id: str, session_id: str | None):
	"""
	publish using user, session_id, item_id
	"""
	delta = chunk.choices[0].delta
	logger.debug(
		{
			"message": "_stream_chunk",
			"id": item_id,
			"session_id": session_id,
			"delta": delta.to_json(indent=None),
		}
	)

	cc = ContentChunk(
		type="text",
		message="content",
		content="",
		item_id=item_id,
		session_id=session_id or "",
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

	return cc


def _get_end_reason(completion_response: dict):
	comp = completion_response.get("choices", [{}])[0]
	if comp.get("finish_reason") == "tool_use" or comp.get("finish_reason") == "tool_calls":
		return "tool_use"

	if comp.get("finish_reason") == "stop":
		return "turn_end"

	return None


def _set_key(model: str) -> str | None:
	provider = get_provider(model)
	if not provider:
		return f"Model {model} not supported"

	key, value = get_key(provider)
	if not key:
		return f"Model {model} not supported"

	if not value:
		return f"API key {key} not set"

	os.environ[key] = value
	return None


def _should_preserve_thinking(model: str):
	# reference: https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking?q=thinking#preserving-thinking-blocks
	return "sonnet" in model or "opus" in model


def _get_thinking(thinking_effort: ReasoningEffort | None):
	# Used by Gemini and Anthropic models
	if thinking_effort is None:
		return None

	return {"type": "enabled", "budget_tokens": DEFAULT_REASONING_BUDGET_MAP[thinking_effort]}


def _get_inter_chunk_latency(timestamps: list[float]):
	diffs = []
	for i in range(1, len(timestamps)):
		diffs.append(timestamps[i] - timestamps[i - 1])

	return sum(diffs) / len(diffs)
