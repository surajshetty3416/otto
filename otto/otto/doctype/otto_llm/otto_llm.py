from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
import json
from typing import TYPE_CHECKING, cast

import frappe
import frappe.realtime
from frappe.model.document import Document

from otto.llm.utils import DEFAULT_INSTRUCTION

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
		size: DF.Literal["Very Small", "Small", "Medium", "Large"]
		supports_images: DF.Check
		title: DF.Data
	# end: auto-generated types

	@staticmethod
	def new(
		name: str,
		title: str,
		provider: str,
		is_reasoning: bool = False,
		size: str | None = None,
		supports_images: bool = False,
	):
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
	def ask(self, query: str, instruction: str | None = None, reasoning_effort: str | None = None):
		"""Test the LLM with a query and system prompt."""
		from otto.lib import quick_query

		assert self.name is not None, "type check"

		try:
			stream = quick_query(
				query,
				model=self.name,
				instruction=instruction or DEFAULT_INSTRUCTION,
				reasoning_effort=get_reasoning_effort(reasoning_effort, self),
			)

			for chunk in stream:
				frappe.realtime.publish_realtime(
					f"stream-llm-{self.name}",
					{
						"llm": self.name,
						"chunk": chunk,
					},
				)
		except Exception as e:
			return json.dumps({"error": str(e)})

		return {"message": "success"}


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
