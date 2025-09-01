# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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

	@staticmethod
	def chat(session: str | None = None, message: str | None = None): ...

	def get_instruction(self): ...
