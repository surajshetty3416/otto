# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OttoAssistantToolCT(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		is_enabled: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		properties: DF.JSON | None
		required: DF.JSON | None
		requires_permission: DF.Check
		slug: DF.Data | None
		title: DF.Data | None
		tool: DF.Link | None
	# end: auto-generated types

	pass
