from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from typing import cast

import frappe
from frappe.model.document import Document


class OttoScrapbook(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		content: DF.Code | None
		execution: DF.Link | None
		task: DF.Link | None
		tool: DF.Link | None
	# end: auto-generated types

	@staticmethod
	def new(content: str, *, execution: str | None = None, task: str | None = None, tool: str | None = None):
		doc = cast(
			OttoScrapbook,
			frappe.get_doc(
				{
					"doctype": "Otto Scrapbook",
					"content": content,
					"execution": execution,
					"task": task,
					"tool": tool,
				}
			),
		)
		doc.save(ignore_permissions=True)
		return doc
