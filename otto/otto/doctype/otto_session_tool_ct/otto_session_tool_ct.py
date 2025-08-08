# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

# import frappe
import json
from typing import cast

import frappe
from frappe.model.document import Document

from otto.llm.types import ToolSchema, ToolSchemaParameters


class OttoSessionToolCT(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText
		is_enabled: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		properties: DF.JSON | None
		required: DF.JSON | None
		slug: DF.Data
	# end: auto-generated types

	_schema: ToolSchema | None = None

	@staticmethod
	def new(tool_schema: ToolSchema):
		doc = cast("OttoSessionToolCT", frappe.new_doc("Otto Session Tool CT"))
		doc.slug = tool_schema["name"]
		doc.description = tool_schema["description"]
		doc.properties = json.dumps(tool_schema["parameters"].get("properties", {}), indent=2)
		doc.required = json.dumps(tool_schema["parameters"].get("required", []))
		return doc

	@property
	def schema(self) -> ToolSchema:
		if self._schema is not None:
			return self._schema

		parameters = ToolSchemaParameters(
			type="object",
			properties={},
			required=[],
		)

		if self.properties:
			parameters["properties"] = json.loads(self.properties)

		if self.required:
			parameters["required"] = json.loads(self.required)

		self._schema = ToolSchema(
			name=self.slug,
			description=self.description,
			parameters=parameters,
		)
		return self._schema

	def get_schema(self):
		return {"type": "function", "function": self.schema}
