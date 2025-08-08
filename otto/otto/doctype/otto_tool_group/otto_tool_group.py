# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

from typing import cast

import frappe
from frappe.model.document import Document


class OttoToolGroup(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
	# end: auto-generated types

	@staticmethod
	def new(name: str, description: str | None = None):
		doc = cast(
			"OttoToolGroup",
			frappe.get_doc(
				{
					"doctype": "Otto Tool Group",
					"name": name,
					"description": description,
				}
			),
		)

		doc.save()
		return doc
