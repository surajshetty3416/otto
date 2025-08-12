# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

from typing import Any, Literal, TypedDict, cast
from urllib.parse import unquote

import frappe
from frappe.model.document import Document

import otto


class LogResponse(TypedDict):
	message: Literal["success", "error"]
	reason: str | None  # set if message is "error"
	feedback: OttoFeedback | None  # OttoFeedback document


class OttoFeedback(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		comment: DF.SmallText | None
		session: DF.Link | None
		value: DF.Int
	# end: auto-generated types

	@staticmethod
	def new(
		*,
		value: Any,  # "1", "-1", "0" or 1, -1, 0, else defaults to 0
		session: str | None = None,
		comment: str | None = None,
	):
		"""Create a new feedback."""
		doc = cast("OttoFeedback", frappe.get_doc({"doctype": "Otto Feedback"}))
		doc.session = session
		doc.value = get_value(value) or 0
		doc.comment = unquote(comment) if comment else None
		doc.save(ignore_permissions=True, ignore_version=True)
		return doc

	@staticmethod
	def log(
		*,
		name: str | None = None,
		value: Any | None = None,  # "1", "-1", "0" or 1, -1, 0, else defaults to 0
		session: str | None = None,
		comment: str | None = None,
	):
		"""Create a new feedback or update an existing one."""
		if not name and (session or comment or value is not None):
			feedback = OttoFeedback.new(session=session, value=value, comment=comment)
			return LogResponse(
				message="success",
				feedback=feedback,
				reason=None,
			)

		if not name:
			# If name is not provided then it's not an update
			return LogResponse(
				message="error",
				reason="Feedback value, comment, or session is required",
				feedback=None,
			)

		feedback = otto.get(OttoFeedback, name)

		if session and feedback.session and feedback.session != session:
			return LogResponse(
				message="error",
				reason=f"Feedback ({name}) already exists for another session ({feedback.session})",
				feedback=None,
			)

		if value is not None:
			feedback.value = value

		if comment is not None:
			feedback.comment = unquote(comment)

		if session is not None:
			feedback.session = session

		feedback.save(ignore_permissions=True)
		return LogResponse(
			message="success",
			feedback=feedback,
			reason=None,
		)

	def before_save(self):
		self.value = max(min(self.value, 1), -1)


def get_value(value: Any) -> Literal[-1, 0, 1] | None:
	if isinstance(value, str):
		value = int(value)

	if isinstance(value, int) and value in [-1, 0, 1]:
		return value  # type: ignore

	return None
