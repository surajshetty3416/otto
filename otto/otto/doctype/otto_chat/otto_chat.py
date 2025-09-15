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
		chat: str | None = None,  # if None, then new chat
		assistant: str | None = None,  # should be present if chat is None
	):
		if chat:
			doc = otto.get(OttoChat, chat)
		else:
			assert assistant, "sanity check"
			doc = OttoChat.new(assistant)

		frappe.enqueue_doc(
			doctype="Otto Chat",
			name=doc.name,
			doc=doc,
			method="interact",
			timeout=300,
			at_front=True,
			# params
			query=query,
		)

	def interact(self, query: Query):
		# TODO:
		# - publish chunks
		# - publish final complete item with end message
		# - if error, publish error
		response = self.session_.interact(query, stream=True)
		for _ in response:
			frappe.publish_realtime()

	@staticmethod
	def new(assistant: str) -> OttoChat:
		from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant

		assistant_doc = otto.get(OttoAssistant, assistant)
		doc = cast(
			"OttoChat",
			frappe.get_doc(
				{
					"doctype": "Otto Chat",
					"assistant": assistant,
				}
			),
		)

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
