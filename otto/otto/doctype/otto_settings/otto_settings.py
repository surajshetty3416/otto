# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OttoSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		anthropic_api_key: DF.Password | None
		gemini_api_key: DF.Password | None
		global_env: DF.JSON | None
		is_enabled: DF.Check
		max_llm_calls: DF.Int
		openai_api_key: DF.Password | None
		task_execution_timeout: DF.Int
	# end: auto-generated types

	pass
