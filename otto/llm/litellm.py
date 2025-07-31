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
from collections.abc import Generator
from typing import TYPE_CHECKING, NamedTuple, cast

import otto
from otto.llm.format import get_messages
from otto.llm.types import (
	Content,
	ContentChunk,
	InteractResponse,
	ReasoningEffort,
	Session,
	SessionItem,
	TextContent,
	ThinkingContent,
	ToolUseContent,
	UserContent,
)
from otto.llm.utils import (
	get_agent_item,
	get_session,
	get_session_list,
	to_content,
	update_session,
)

if TYPE_CHECKING:
	from datetime import datetime

	from litellm import CustomStreamWrapper
	from litellm.types.utils import ModelResponseStream


DEFAULT_LLM = "gemini/gemini-2.5-flash-preview-05-20"
MAX_RETRIES = 6

logger = otto.logger("otto_litellm", "INFO")
DEFAULT_REASONING_BUDGET_MAP: dict[ReasoningEffort, int] = {
	"low": 4096,
	"medium": 8192,
	"high": 16384,
}


class StreamReturn(NamedTuple):
	chunks: list[ContentChunk]
	signature: str | None


class InteractReturn(NamedTuple):
	response: InteractResponse | None
	reason: None | str


def interact(
	# query should be None only if session is provided with a call call update
	query: str | list[str | UserContent] | list[UserContent] | None = None,
	*,
	session: Session | None = None,
	model: str | None = None,
	system: str | None = None,
	tools: list[dict] | None = None,
	reasoning_effort: ReasoningEffort | None = None,
) -> Generator[ContentChunk, None, InteractReturn]:
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
		InteractReturn:
			- On success, `InteractReturn.response` contains an `InteractResponse`
			  object with the generated agent response item, the updated session,
			  and a list of content chunks from the stream. `InteractReturn.reason` is `None`.
			- On failure (e.g., API key issue), `InteractReturn.response` is `None`
			  and `InteractReturn.reason` contains reason for failure.
	"""
	import litellm

	assert query is not None or session is not None, (
		"session (with tool result) is required if query is not provided"
	)

	content = None if query is None else to_content(query)
	model = model or DEFAULT_LLM

	# Creates a new session if session is None, else uses a copy
	update = get_session(content, session)
	session_id = update["id"]

	if reason := _set_key(model):
		return InteractReturn(None, reason)

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

	items = get_session_list(update)
	messages, last_id = get_messages(
		items,
		system,
		preserve_thinking=_should_preserve_thinking(model),
	)

	think = {}
	if reasoning_effort:
		think["reasoning_effort"] = reasoning_effort

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
	signature = None

	# Iterates over the completion stream and returns a list of ContentChunk
	stream_generator = _stream(completion, item, session_id)
	while True:
		try:
			yield next(stream_generator)
		except StopIteration as e:
			chunks, signature = cast(StreamReturn, e.value)
			break

	logger.debug(
		{
			"message": "waiting for callback",
			"id": item["id"],
			"signature": signature,
			"chunks": len(chunks),
		}
	)
	# Wait until the success callback is called
	done.wait()

	logger.debug(
		{
			"message": "after wait",
			"signature": signature,
			"content_len": len(item["content"]),
			"thinking_content": [c for c in item["content"] if c["type"] == "thinking"],
		}
	)

	# Rest of the item updation is handled in litellm.success_callback
	# Thinking signature is required by anthropic
	if signature:
		for c in item["content"]:
			if c["type"] == "thinking":
				c["signature"] = signature

	logger.debug({"message": "updating session", "id": item["id"]})
	# Update the update session with the item
	update_session(update, last_id, item)

	item["meta"]["end_time"] = time.time()

	response = InteractResponse(item=item, update=update, chunks=chunks)
	return InteractReturn(response, None)


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
	signature = None
	chunks: list[ContentChunk] = []

	for chunk in completion:
		if cc := _stream_chunk(chunk, item["id"], session_id):
			logger.debug({"id": item["id"], "content": cc["content"]})
			chunks.append(cc)
			yield cc

		signature = signature or _get_signature(chunk)
	return StreamReturn(chunks, signature)


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
	from frappe.utils.password import get_decrypted_password

	if model.startswith("openai"):
		key = "OPENAI_API_KEY"
	elif model.startswith("anthropic"):
		key = "ANTHROPIC_API_KEY"
	elif model.startswith("gemini"):
		key = "GEMINI_API_KEY"
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
	if not (delta := chunk.choices[0].delta):
		return None

	# Check thinking blocks for signature
	thinking_blocks = delta.get("thinking_blocks")
	if signature := _get_signature_from_thinking_blocks(thinking_blocks):
		return signature

	# Check provider specific fields for signature
	provider_fields = delta.get("provider_specific_fields") or {}
	if (signature := provider_fields.get("signature")) and isinstance(signature, str):
		return signature

	thinking_blocks = provider_fields.get("thinking_blocks")
	if signature := _get_signature_from_thinking_blocks(thinking_blocks):
		return signature

	return None


def _get_signature_from_thinking_blocks(blocks):
	if not blocks or not isinstance(blocks, list):
		return None

	block = blocks[0] or {}
	if (signature := block.get("signature")) and isinstance(signature, str):
		return signature

	return None


def _should_preserve_thinking(model: str):
	# rn only Sonnet 3.7 requires reasoning to be preserved
	# reference: https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking?q=thinking#preserving-thinking-blocks
	return "sonnet" in model or "opus" in model


def _get_thinking(thinking_effort: ReasoningEffort | None):
	# Used by Gemini and Anthropic models
	if thinking_effort is None:
		return None

	return {"type": "enabled", "budget_tokens": DEFAULT_REASONING_BUDGET_MAP[thinking_effort]}
