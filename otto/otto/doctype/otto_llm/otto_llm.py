from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
import json
from typing import TYPE_CHECKING, cast

import frappe
from frappe.model.document import Document

if TYPE_CHECKING:
	from otto.llm.types import ReasoningEffort


class OttoLLM(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		is_reasoning: DF.Check
		provider: DF.Literal["Anthropic", "OpenAI", "Google"]
		title: DF.Data
	# end: auto-generated types

	@staticmethod
	def new(name: str, title: str, provider: str, is_reasoning: bool = False):
		doc = cast(
			OttoLLM,
			frappe.get_doc(
				{
					"doctype": "Otto LLM",
					"name": name,
					"title": title,
					"provider": provider,
					"is_reasoning": is_reasoning,
				}
			),
		)

		doc.save()
		return doc

	@frappe.whitelist()
	def ask(self, query: str, system: str | None = None, reasoning_effort: str | None = None):
		"""Test the LLM with a query and system prompt."""
		from otto.llm import interact

		system = system or "You are a helpful assistant."

		result, reason = interact(
			query,
			model=self.name,
			system=system,
			reasoning_effort=get_reasoning_effort(reasoning_effort, self),
		)
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


def get_reasoning_effort(effort: str | None, llm: OttoLLM | None = None) -> ReasoningEffort | None:
	if not effort:
		return None

	if llm and not llm.is_reasoning:
		return None

	if effort in ["low", "medium", "high"]:
		return cast("ReasoningEffort", effort)

	return {
		"None": None,
		"Low": "low",
		"Medium": "medium",
		"High": "high",
	}.get(effort, None)
