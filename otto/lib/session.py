from __future__ import annotations

from typing import Literal, cast, overload

import otto
from otto.lib.errors import InteractionError
from otto.lib.types import (
	Content,
	ContentChunk,
	InteractResponse,
	PendingToolUse,
	Query,
	ReasoningEffort,
	SessionItem,
	SessionStats,
	ToolSchema,
	ToolUseContent,
	ToolUseUpdate,
)
from otto.llm import utils
from otto.otto.doctype.otto_session.otto_session import OttoSession, SessionInteractStream
from otto.utils import drain

__all__ = [
	"Session",
	"load",
	"new",
	"quick_query",
]


class Session:
	"""High-level wrapper for the `OttoSession` DocType.

	This class provides a simplified interface for managing and interacting with
	an LLM session. It handles the underlying database document operations,
	allowing developers to focus on the interaction logic.

	A `Session` instance should not be created directly. Instead, use the
	`Session.new()` static method to create a new session or `Session.load()`
	to resume an existing one.
	"""

	_session: OttoSession

	@staticmethod
	def new(
		model: str = utils.DEFAULT_MODEL,
		instruction: str = utils.DEFAULT_INSTRUCTION,
		reasoning_effort: ReasoningEffort | None = None,
		tools: list[ToolSchema] | None = None,
	) -> Session:
		# See session.new for details
		manager = Session()

		manager._session = OttoSession.new(
			model=model,
			instruction=instruction,
			reasoning_effort=reasoning_effort,
			tools=tools,
		)
		return manager

	@staticmethod
	def load(id: str) -> Session:
		# See session.load for details
		manager = Session()
		manager._session = otto.get(OttoSession, id)
		return manager

	@property
	def id(self) -> str:
		"""The unique identifier of the session."""
		assert self._session.name is not None, "type check"
		return self._session.name

	@property
	def failure_reason(self) -> str | None:
		"""The reason for session failure, if any. `None` otherwise."""
		return self._session.reason

	@property
	def is_active(self) -> bool:
		"""Returns `True` if the session is currently active.

		A session is considered active if it is currently processing a query
		or waiting for an LLM response.
		"""
		return bool(self._session.is_active)

	@property
	def model(self) -> str:
		"""The LLM model used for this session."""
		assert self._session.llm is not None, "type check"
		return self._session.llm

	def set_model(self, model_id: str) -> None:
		"""Set the LLM model for this session."""
		self._session.llm = model_id
		self.save()

	@property
	def instruction(self) -> str:
		"""The instruction used for this session."""
		assert self._session.instruction is not None, "type check"
		return self._session.instruction

	def set_instruction(self, instruction: str) -> None:
		"""Set the instruction for this session."""
		self._session.instruction = instruction
		self.save()

	@property
	def reasoning_effort(self) -> ReasoningEffort | None:
		"""The reasoning effort used for this session."""
		assert self._session.reasoning_effort is not None, "type check"
		reasoning_effort = self._session.reasoning_effort
		if utils.is_reasoning_effort(reasoning_effort):
			return reasoning_effort

		return None

	def set_reasoning_effort(self, reasoning_effort: ReasoningEffort | None) -> None:
		"""Set the reasoning effort for this session."""
		if reasoning_effort is None:
			self._session.reasoning_effort = "None"
		else:
			self._session.reasoning_effort = reasoning_effort
		self.save()

	@property
	def tools(self) -> list[ToolSchema]:
		"""The tools used for this session."""
		return [tool.schema for tool in self._session.tools]

	def set_tools(self, tools: list[ToolSchema]) -> None:
		"""Set the tools for this session."""
		self._session.set_tools(tools)
		self.save()

	@overload
	def interact(self, query: Query | None = None, *, stream: Literal[False]) -> InteractResponse: ...

	@overload
	def interact(self, query: Query | None = None, *, stream: Literal[True]) -> InteractStreamResponse: ...

	def interact(
		self,
		query: Query | None = None,
		*,
		stream: bool = True,
	) -> InteractStreamResponse | InteractResponse:
		"""Performs one turn of interaction with the LLM.

		This method sends the user's query, along with the current session
		context (history and tools), to the LLM. It then updates the session
		with the LLM's full response upon completion.

		The caller is responsible for creating an interaction loop. This method
		only represents a single API call. After this, the caller should execute
		any tool use requests, update the session using `Session.update_tool_use()`
		and invoke this method again to continue the conversation.

		Args:
		    query: The user's input for this turn. Can be a string, a list of
		        content blocks. Value may be `None` if interact is being called
				after a tool use update.
		    stream: If `True`, streams the response as `ContentChunk` objects.
		        If `False`, returns.

		Returns:
		    If `stream` is `True`, returns an `InteractStreamResponse` object that yields
		    `ContentChunk`s. The full response is available on the `item` property after iterating.
		    If `stream` is `False`, returns an `InteractResponse` tuple `(interaction, reason)` directly.
		"""
		interact_generator = self._session.interact(query)

		if not stream:
			return drain(interact_generator)
		return InteractStreamResponse(interact_generator)

	def get_pending_tool_use(self, last_item_only: bool = True) -> list[PendingToolUse]:
		"""Retrieves a list of tool use requests that are pending execution.

		After an `interact()` call, the LLM may request to use one or more
		tools.  This method extracts those requests so the caller can execute
		them. After doing so `Session.update_tool_use()` should be called to
		update the session with the results.

		Args:
		    last_item_only: If `True`, only scans the last item in the session
		        for pending tool uses. If `False`, scans all items.

		Returns:
		    A list of `PendingToolUse` objects, each representing a tool call
		    that needs to be executed.
		"""
		pending: list[PendingToolUse] = []

		if last_item_only and (item := self.get_last_item()) is None:
			return pending

		if last_item_only:
			last_item = self.get_last_item()
			assert last_item is not None, "type check"
			search_items = [last_item]
		else:
			search_items = self.get_items()

		for item in search_items:
			for content in item["content"]:
				if content["type"] != "tool_use" or content["status"] != "pending":
					continue

				pending.append(
					PendingToolUse(
						id=content["id"],
						name=content["name"],
						args=_get_args_from_tool_use_content(content),
					)
				)

		return pending

	def update_tool_use(self, update: ToolUseUpdate | list[ToolUseUpdate]) -> None:
		"""Updates the status and result of given tool use within this session.

		After executing a tool requested by the LLM (see `Session.get_pending_tool_use()`),
		this method should be called to provide the result back to the session. This
		result will be included in the context for the next `interact()` call.

		Args:
		    update: A single `ToolUseUpdate` object or a list of them,
		        containing the ID of the tool use and its result.
		"""
		if (session := self._session._get_session()) is None:
			return

		utils.update_tool_use(session=session, update=update)
		self._session._set_session(session)

	def get_last_item(self) -> SessionItem | None:
		"""Returns the most recent item from the session's interaction history.

		A session item can be a user message, an agent's response, or a tool
		call result.

		Returns:
		    The last `SessionItem` in the history, or `None` if the session is empty.
		"""
		return self._session.get_last_item()

	def get_last_response(self) -> list[Content] | None:
		"""Returns the last agent response from the session. If last item is not
		an agent response, returns `None`.

		Returns:
		    A list of `Content` objects, or `None`.
		"""
		item = self.get_last_item()
		if item is None or item["meta"]["role"] != "agent":
			return None

		return item["content"]

	def get_items(self) -> list[SessionItem]:
		"""Returns all items in the session's interaction history in order.

		This provides the full chronological record of the conversation.

		Returns:
		    A list of all `SessionItem` objects in the session.
		"""
		if (session := self._session._get_session()) is None:
			return []

		return utils.get_sequence(session)

	def get_stats(self) -> SessionStats | None:
		return self._session.get_stats()

	def get_llm_call_count(self) -> int:
		"""Returns the total number of calls made to the LLM in this session."""
		return self._session.get_llm_call_count()

	def save(self) -> None:
		"""Save the session to the database."""
		self._session.save(ignore_permissions=True)


class InteractStreamResponse:
	"""A wrapper for a streaming interaction that provides access to the final
	aggregated response after the stream has been consumed.
	"""

	_stream: SessionInteractStream
	_item: SessionItem | None
	_failure_reason: str | None

	@property
	def item(self) -> SessionItem | None:
		return self._item

	@property
	def content(self) -> list[Content]:
		if self._item is None:
			return []

		return self._item["content"]

	@property
	def failure_reason(self) -> str | None:
		return self._failure_reason

	def __init__(self, stream: SessionInteractStream):
		self._stream = stream
		self._item = None
		self._failure_reason = None

	def __iter__(self):
		return self

	def __next__(self) -> ContentChunk:
		try:
			return next(self._stream)
		except StopIteration as e:
			item, reason = cast("InteractResponse", e.value)
			self._item = item
			self._failure_reason = reason
			raise StopIteration  # noqa: B904


@overload
def quick_query(
	query: Query,
	*,
	model: str = utils.DEFAULT_MODEL,
	instruction: str = utils.DEFAULT_INSTRUCTION,
	reasoning_effort: ReasoningEffort | None = None,
	tools: list[ToolSchema] | None = None,
	stream: Literal[True] = True,
) -> InteractStreamResponse: ...


@overload
def quick_query(
	query: Query,
	*,
	model: str = utils.DEFAULT_MODEL,
	instruction: str = utils.DEFAULT_INSTRUCTION,
	reasoning_effort: ReasoningEffort | None = None,
	tools: list[ToolSchema] | None = None,
	stream: Literal[False] = False,
) -> list[Content]: ...


def quick_query(
	query: Query,
	*,
	# Interaction config
	model: str = utils.DEFAULT_MODEL,
	instruction: str = utils.DEFAULT_INSTRUCTION,
	tools: list[ToolSchema] | None = None,
	reasoning_effort: ReasoningEffort | None = None,
	# Determines the output type, see overloads
	stream: bool = True,
) -> InteractStreamResponse | list[Content]:
	"""Convenience function to be used for one-off queries.

	This is a convenience function that creates a new session and immediately
	interacts with it.

	For more control use `Session.new|load` then `Session.interact`.

	The behavior and return type varies based on the `stream` parameter:

	- With `stream=True`: Returns an `InteractStreamResponse` instance.
	- With `stream=False`: Returns just the response content (list[Content])

	Args:
		query: The query to send to the LLM
		model: The identifier of the LLM to use
		instruction: The system prompt or instruction for the LLM
		reasoning_effort: The reasoning effort level for the LLM
		tools: A list of tool schemas available to the LLM
		stream: Whether to stream the response

	Returns:
		Either a response stream or content list depending on the stream parameter

	Raises:
		InteractionError: If the interaction fails or returns no response
	"""
	session = Session.new(
		model=model,
		instruction=instruction,
		reasoning_effort=reasoning_effort,
		tools=tools,
	)

	if stream:
		return session.interact(query, stream=True)

	interaction, reason = session.interact(query, stream=False)
	if reason or interaction is None:
		raise InteractionError(reason or "Unknown error, did not receive a response")

	return interaction["content"]


def new(
	model: str = utils.DEFAULT_MODEL,
	instruction: str = utils.DEFAULT_INSTRUCTION,
	reasoning_effort: ReasoningEffort | None = None,
	tools: list[ToolSchema] | None = None,
) -> Session:
	"""Creates a new LLM session.

	Args:
		model: The identifier of the LLM to use for this session.
		instruction: The system prompt or instruction for the LLM.
		reasoning_effort: The reasoning effort level for the LLM.
		tools: A list of tool schemas available to the LLM during this session.

	Returns:
		A new `Session` instance.
	"""
	return Session.new(model, instruction, reasoning_effort, tools)


def load(id: str) -> Session:
	"""Loads an existing LLM session from the database.

	Args:
		id: The unique identifier of the session to load.

	Returns:
		A `Session` instance corresponding to the given ID.
	"""
	return Session.load(id)


def _get_args_from_tool_use_content(content: ToolUseContent) -> dict:
	if not content["override"]:
		return content["args"]

	return {**content["args"], **content["override"]}
