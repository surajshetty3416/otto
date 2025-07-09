# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OttoSessionItemCT(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		content: DF.JSON
		cost: DF.Float
		end_reason: DF.Data | None
		end_time: DF.Datetime | None
		input_tokens: DF.Int
		model: DF.Data | None
		next: DF.Data | None
		output_tokens: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		role: DF.Data
		selected: DF.Int
		start_time: DF.Datetime | None
		timestamp: DF.Datetime
		uid: DF.Data
	# end: auto-generated types

	pass
