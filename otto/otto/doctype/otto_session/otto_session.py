# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, NamedTuple, cast

import frappe
from frappe.model.document import Document

import otto
from otto import llm
from otto.llm.types import ContentChunk, Query, Session, ToolSchema
from otto.llm.utils import get_last_id, get_sequence
from otto.otto.doctype.otto_session_tool_ct.otto_session_tool_ct import OttoSessionToolCT

if TYPE_CHECKING:
	from otto.llm.litellm import InteractReturnTuple
	from otto.llm.types import SessionItem

logger = otto.logger("otto.doctype.otto_session", level="DEBUG")


class InteractResponse(NamedTuple):
	item: SessionItem | None
	failure_reason: str | None


SessionInteractStream = Generator[ContentChunk, None, InteractResponse]


class OttoSession(Document):
	"""Represents a single session with an LLM.

	Session is purpose agnostic, it may be a turn-based chat or a task handled
	entirely by the LLM.

	This DocType acts as a persistent wrapper around the in-memory session
	representation used by the `otto.llm` module.

	OttoSession is not meant to be used directly, use the wrapper
	`otto.lib.Session` instead, this exposes specific convenience functions to
	handle a session. View `OttoExecution` for an example on how it's used.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_session_item_ct.otto_session_item_ct import OttoSessionItemCT
		from otto.otto.doctype.otto_session_tool_ct.otto_session_tool_ct import OttoSessionToolCT

		first: DF.Data | None
		instruction: DF.Code | None
		is_active: DF.Check
		items: DF.Table[OttoSessionItemCT]
		llm: DF.Link | None
		reason: DF.SmallText | None
		reasoning_effort: DF.Literal["None", "Low", "Medium", "High"]
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		tools: DF.Table[OttoSessionToolCT]
		uid: DF.Data | None
	# end: auto-generated types

	_osi_map: dict[str, OttoSessionItemCT] | None = None
	_last_item: SessionItem | None = None
	_session: Session | None = None

	@staticmethod
	def new(
		*,
		model: str,
		instruction: str,
		reasoning_effort: str | None,
		tools: list[ToolSchema] | None = None,
		reference_doctype: str | None = None,
		reference_name: str | None = None,
	):
		doc = cast("OttoSession", frappe.get_doc({"doctype": "Otto Session"}))

		doc.llm = model
		doc.instruction = instruction
		if reasoning_effort and reasoning_effort in ["None", "Low", "Medium", "High"]:
			doc.reasoning_effort = reasoning_effort  # type: ignore
		else:
			doc.reasoning_effort = "None"

		if reference_doctype:
			doc.reference_doctype = reference_doctype

		if reference_name and reference_doctype:
			doc.reference_name = reference_name

		doc.set_tools(tools or [])
		doc.save(ignore_permissions=True, ignore_version=True)
		return doc

	def interact(self, query: Query | None = None) -> SessionInteractStream:
		"""Performs one turn of interaction with the LLM, streaming the response.

		This method sends the user's query, along with the current session
		context (history and tools), to the LLM. It then updates the session
		with the LLM's full response upon completion.

		The caller is responsible for creating an interaction loop. This method
		only represents a single API call. After this, the caller should execute
		the tool use requests and invoke this again.

		Args:
		    query: The user's input for this turn. Can be a string, a list of
		        strings, or None to let the LLM continue its turn.

		Yields:
		    ContentChunk: Chunks of the LLM's response in real-time.

		Returns:
		    On completion, returns a tuple containing the latest session item
		    and an error reason.
		    - `(SessionItem, None)` on success.
		    - `(None, str)` on failure, where the string is the error reason.
		"""
		from otto.otto.doctype.otto_llm.otto_llm import get_reasoning_effort

		self._set_status(is_active=True)
		interact_generator = llm.interact(
			query,  # type: ignore needed cause not strong enough type system
			session=self._get_session(),
			tools=[t.get_schema() for t in self.tools],
			model=self.llm,
			system=self.instruction,
			reasoning_effort=get_reasoning_effort(self.reasoning_effort),
		)

		while True:
			try:
				yield next(interact_generator)
			except StopIteration as e:
				interaction, reason = cast("InteractReturnTuple", e.value)
				logger.info(
					{
						"message": "interact success",
						"session": self.name,
						"session_size": interaction and len(interaction["update"]),
						"item": interaction and interaction["item"],
					}
				)
				break
			except Exception as e:
				otto.log_error(title="interact error", doc=self)
				reason = f"Interaction errored out: {e}"
				self._set_status(is_active=False, reason=reason)
				return InteractResponse(None, reason)

		if interaction is None:
			reason = reason or "No interaction returned"
			self._set_status(is_active=False, reason=reason)
			return InteractResponse(None, reason)

		self._set_status(is_active=False, session=interaction["update"])

		self._last_item = interaction["item"]
		return InteractResponse(self._last_item, None)

	def get_last_item(self) -> SessionItem | None:
		if self._last_item:
			return self._last_item

		session = self._get_session()
		if session is None:
			return None

		id = get_last_id(session)
		return session["items"].get(id)

	def set_tools(self, tools: list[ToolSchema]):
		self.tools.clear()
		for tool in tools:
			self.append("tools", OttoSessionToolCT.new(tool))

	def _set_status(
		self,
		is_active: bool,
		*,
		reason: str | None = None,
		session: Session | None = None,
	):
		self.is_active = is_active
		self.reason = reason
		if session is not None:
			self._set_session(session)

		self.save(ignore_permissions=True, ignore_version=True)
		frappe.db.commit()

	def _get_session(self) -> None | Session:
		if not self.uid or not self.first:
			# no session yet, will be created on first interaction
			return None

		if self._session is not None:
			return self._session

		session = Session(
			id=self.uid,
			first=self.first,
			items={},
		)

		self._set_osi_map()
		assert self._osi_map is not None, "type check"
		for item in self.items:
			self._osi_map[item.uid] = item
			session["items"][item.uid] = item.to_session_item()
		self._session = session

		return session

	def _set_session(self, session: Session) -> None:
		from otto.otto.doctype.otto_session_item_ct.otto_session_item_ct import OttoSessionItemCT

		self.uid = session["id"]
		self.first = session["first"]
		self._session = session

		# reset sequence incase active list has changed
		self.items.clear()
		added = set()
		self._set_osi_map()
		assert self._osi_map is not None, "type check"

		# Active sequence items first
		for item in get_sequence(session):
			osi = self._osi_map.get(item["id"])
			if not osi:
				osi = OttoSessionItemCT.from_session_item(item)
			else:
				osi.sync_with_session_item(item)
			osi.is_selected = True
			added.add(item["id"])
			self.append("items", osi)

		# Rest of the non-active items
		for uid, item in session["items"].items():
			if uid in added:
				continue

			osi = self._osi_map.get(uid)
			if not osi:
				osi = OttoSessionItemCT.from_session_item(item)
			else:
				osi.sync_with_session_item(item)

			osi.is_selected = False
			self.append("items", osi)

		self.save(ignore_permissions=True, ignore_version=True)
		frappe.db.commit()

	def get_llm_call_count(self, selected: bool = False):
		"""
		If selected is True, returns the number of LLM calls in the selected items.
		If selected is False returns total count including selected and non-selected items.
		"""
		count = 0
		for item in self.items:
			if (selected and not item.is_selected) or item.role != "agent":
				continue

			count += 1
		return count

	@frappe.whitelist()
	def get_stats(self):
		if not (session := self._get_session()):
			return None

		return llm.get_stats(session)

	def _set_osi_map(self) -> None:
		"""Sets _osi_map (OttoSessionItemCT) if not already set, should be used only in get_session and set_session"""
		if hasattr(self, "_osi_map") and self._osi_map is not None:
			return
		self._osi_map = {}
