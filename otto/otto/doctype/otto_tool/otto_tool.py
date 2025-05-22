# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

# import frappe
import json
from typing import Any

import frappe
from frappe.exceptions import ValidationError
from frappe.model.document import Document

from otto.utils import execute

arg_type_to_json_type = {
	"str": "string",
	"int": "integer",
	"float": "number",
	"bool": "boolean",
	"list": "array",
	"dict": "object",
}


class OttoTool(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_tool_arg_ct.otto_tool_arg_ct import OttoToolArgCT

		args: DF.Table[OttoToolArgCT]
		code: DF.Code
		description: DF.LongText | None
		is_valid: DF.Check
		reason: DF.SmallText | None
		slug: DF.Data
	# end: auto-generated types

	def before_save(self):
		reasons, args_def = execute.validate(self.code, self.slug)
		if reasons:
			self.is_valid = False
			self.reason = "\n".join(reasons)
			return

		self.is_valid = True
		self.reason = None

		self.args = []
		for arg in args_def:
			self.append(
				"args",
				{
					"arg_name": arg["name"],
					"type": arg_type_to_json_type[arg["type"]],
					"description": "",
					"is_required": not arg["has_default"],
				},
			)

	@frappe.whitelist()
	def get_function_schema(self):
		"""Returns function schema for the tool, add meta properties that might aid in usage reasoning."""
		properties = {
			arg.arg_name: {"type": arg.type, "description": arg.description or ""} for arg in self.args
		}

		"""Returns tool as a JSON Schema function"""
		schema = {
			"name": self.slug,
			"description": self.description or "",
			"parameters": {
				"type": "object",
				"properties": {
					"explanation": {
						"type": "string",
						"description": "A short explanation of why the this tool is being called, and how it contributes to the task.",
					},
					**properties,
				},
				"required": [arg.arg_name for arg in self.args if arg.is_required] + ["explanation"],
			},
		}

		return {
			"type": "function",
			"function": schema,
		}

	def execute(self, args: dict[str, Any]):
		if not self.is_valid:
			raise ValidationError("tool is invalid: " + (self.reason or ""))

		arg_names = []
		for arg in self.args:
			assert arg.arg_name is not None, "sanity check"
			arg_names.append(arg.arg_name)

		return execute.execute(self.code, args=args, arg_names=arg_names)

	@frappe.whitelist()
	def test_execute(self, args: dict[str, Any]):
		try:
			result = dict(self.execute(args))
			if not result["stdout"]:
				del result["stdout"]

			if not result["stderr"]:
				del result["stderr"]

			return json.dumps(result, indent=2)
		except Exception as e:
			return f"error: {e}"
