from __future__ import annotations

from typing import Literal, cast, overload

from otto.llm import utils
from otto.utils import drain

"""
Library wrapper around OttoSession
"""

import otto
from otto.lib.types import (
	InteractInput,
	PendingToolUse,
	SessionInteractReturn,
	SessionInteractStream,
	SessionItem,
	ToolSchema,
	ToolUseUpdate,
)
from otto.otto.doctype.otto_session.otto_session import OttoSession


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
		llm: str,
		instruction: str,
		reasoning_effort: str | None,
		tools: list[ToolSchema] | None = None,
	) -> Session:
		"""Creates a new LLM session.

		Args:
		    llm: The identifier of the LLM to use for this session.
		    instruction: The system prompt or instruction for the LLM.
		    reasoning_effort: The reasoning effort level for the LLM.
		    tools: A list of tool schemas available to the LLM during this session.

		Returns:
		    A new `Session` instance.
		"""
		manager = Session()

		manager._session = OttoSession.new(
			llm=llm,
			instruction=instruction,
			reasoning_effort=reasoning_effort,
			tools=tools,
		)
		return manager

	@staticmethod
	def load(id: str) -> Session:
		"""Loads an existing LLM session from the database.

		Args:
		    id: The unique identifier of the session to load.

		Returns:
		    A `Session` instance corresponding to the given ID.
		"""
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

	@overload
	def interact(self, query: InteractInput, *, stream: Literal[False]) -> SessionInteractReturn: ...

	@overload
	def interact(self, query: InteractInput, *, stream: Literal[True]) -> SessionInteractStream: ...

	def interact(
		self,
		query: InteractInput = None,
		*,
		stream: bool = True,
	) -> SessionInteractStream | SessionInteractReturn:
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
		    If `stream` is `True`, returns a generator (`SessionInteractStream`) that
		    yields `ContentChunk`s and returns a `SessionInteractReturn` object.
		    If `stream` is `False`, returns a `SessionInteractReturn` object directly.
		"""
		interact_generator = self._session.interact(query)

		if not stream:
			return drain(interact_generator)

		def _interact():
			# Inner function to prevent outer function from becoming a generator
			while True:
				try:
					yield next(interact_generator)
				except StopIteration as e:
					return cast(SessionInteractReturn, e.value)

		return _interact()

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
						args=content["args"],
					)
				)

		return pending

	def update_tool_use(self, update: ToolUseUpdate | list[ToolUseUpdate]):
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

	def get_items(self) -> list[SessionItem]:
		"""Returns all items in the session's interaction history.

		This provides the full chronological record of the conversation.

		Returns:
		    A list of all `SessionItem` objects in the session.
		"""
		if (session := self._session._get_session()) is None:
			return []

		return utils.get_sequence(session)

	def get_llm_call_count(self) -> int:
		"""Returns the total number of calls made to the LLM in this session."""
		return self._session.get_llm_call_count()
