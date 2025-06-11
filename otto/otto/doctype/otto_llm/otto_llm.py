from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
import json
from typing import cast

import frappe
from frappe.model.document import Document


class OttoLLM(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		provider: DF.Literal["Anthropic", "OpenAI", "Google"]
		title: DF.Data
	# end: auto-generated types

	@staticmethod
	def new(name: str, title: str, provider: str):
		doc = cast(
			OttoLLM,
			frappe.get_doc(
				{
					"doctype": "Otto LLM",
					"name": name,
					"title": title,
					"provider": provider,
				}
			),
		)

		doc.save()
		return doc

	@frappe.whitelist()
	def ask(self, query: str, system: str | None = None):
		"""Test the LLM with a query and system prompt."""
		from otto.llm import interact

		system = system or "You are a helpful assistant."

		result, reason = interact(query, model=self.name, system=system)
		if reason:
			return reason

		assert result is not None, "sanity check"

		try:
			content = result["item"]["content"][-1]

			if content["type"] == "text":
				return content["text"]

			return json.dumps(content, indent=2)
		except Exception:
			return json.dumps(result.get("item", {}).get("content", []), indent=2)
