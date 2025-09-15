# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

from typing import cast

import frappe
from frappe.model.document import Document


class OttoPermission(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		session: DF.Link | None
		status: DF.Literal["Pending", "Granted", "Denied"]
		tool_use_id: DF.Data | None
	# end: auto-generated types

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

	@frappe.whitelist()
	def grant(self):
		self.status = "Granted"
		# Execute tool and update, line up execution resume after tool has run
		self.save()

	@frappe.whitelist()
	def deny(self):
		self.status = "Denied"
		# Update tool use and line up resume
		self.save()
