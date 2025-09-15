# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

import json
from typing import Literal, cast

import frappe
from frappe.model.document import Document

from otto.lib.types import ToolUseContent
from otto.lib.utils import get_tool_use


class OttoPermission(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		session: DF.Link
		status: DF.Literal["Pending", "Granted", "Denied"]
		tool_use_id: DF.Data
	# end: auto-generated types

	_tool_use: ToolUseContent | None = None

	@property
	def tool_use_(self) -> ToolUseContent | None:
		if self._tool_use is None:
			self._tool_use = get_tool_use(self.session, self.tool_use_id)
		return self._tool_use

	@staticmethod
	def new(
		*,
		session: str,
		tool_use_id: str,
	):
		doc = cast("OttoPermission", frappe.get_doc({"doctype": "Otto Permission"}))
		doc.session = session
		doc.tool_use_id = tool_use_id
		doc.status = "Pending"
		doc.save(ignore_permissions=True, ignore_version=True)
		return doc

	@property
	def tool_status(self):
		if not self.tool_use_:
			return "unknown"

		return self.tool_use_["status"]

	@property
	def tool_name(self) -> str:
		if not self.tool_use_:
			return "unknown"

		return self.tool_use_["name"]

	@property
	def tool_use_args(self) -> str:
		if not self.tool_use_:
			return "{}"

		return json.dumps(self.tool_use_["args"], indent=2)

	@property
	def tool_use_result(self) -> str | None:
		if not self.tool_use_:
			return None

		return self.tool_use_["result"]

	@frappe.whitelist()
	def grant(self):
		self.set_status("Granted")
		self.resume()

	@frappe.whitelist()
	def deny(self):
		self.set_status("Denied")
		self.resume()

	def set_status(self, status: Literal["Granted", "Denied"]):
		self.status = status
		self.save()
		# frappe.db.commit()

	def resume(self):
		from otto.otto.doctype.otto_task.otto_task import get_timeout

		execs = frappe.db.get_list(
			"Otto Execution",
			filters={"session": self.session},
			fields=["name"],
			limit=1,
			pluck="name",
		)
		if not execs:
			return

		frappe.enqueue_doc(
			doctype="Otto Execution",
			name=execs[0],
			method="resume",
			timeout=get_timeout(),
		)
