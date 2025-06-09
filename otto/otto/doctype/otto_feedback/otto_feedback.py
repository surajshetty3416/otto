# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OttoFeedback(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		comment: DF.SmallText | None
		execution: DF.Link | None
		value: DF.Int
	# end: auto-generated types

	def before_save(self):
		self.value = max(min(self.value, 1), -1)
