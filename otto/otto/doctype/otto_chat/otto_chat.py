from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

import otto
import otto.lib as lib
from otto.llm.utils import DEFAULT_MODEL

if TYPE_CHECKING:
	from otto.lib.types import Query


class OttoChat(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		assistant: DF.Link
		session: DF.Link
		title: DF.Data | None
	# end: auto-generated types

	_session: lib.Session

	@property
	def session_(self) -> lib.Session:
		if not self._session:
			self._session = lib.load(self.session)
		return self._session

	@session_.setter
	def session_(self, session: lib.Session):
		self._session = session
		self.session = session.id

	@overload
	@staticmethod
	def chat(
		query: Query,
		*,
		chat: None,
		assistant: str,
	): ...

	@overload
	@staticmethod
	def chat(
		query: Query,
		*,
		chat: str,
		assistant: None,
	): ...

	@staticmethod
	def chat(
		query: Query,
		*,
		chat: str | None = None,  # Chat ID, if None, then new chat
		assistant: str | None = None,  # Assistant ID, should be present if chat is None
	):
		if chat:
			doc = otto.get(OttoChat, chat)
		else:
			assert assistant, "sanity check"
			doc = OttoChat.new(assistant)

		return doc.session_.interact(query, stream=True)

	@staticmethod
	def new(assistant: str) -> OttoChat:
		from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant

		doc = cast("OttoChat", frappe.new_doc("Otto Chat"))
		assistant_doc = otto.get(OttoAssistant, assistant)
		doc.assistant = assistant

		reasoning_effort = assistant_doc.reasoning_effort
		if reasoning_effort == "None":
			reasoning_effort = None

		session = lib.new(
			model=assistant_doc.llm or DEFAULT_MODEL,
			instruction=assistant_doc.get_instruction(),
			reasoning_effort=reasoning_effort,
			tools=None,
		)
		doc.session_ = session

		doc.save()
		return doc
