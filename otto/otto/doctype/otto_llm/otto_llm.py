from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from typing import TYPE_CHECKING, cast

import frappe
import frappe.realtime
from frappe.model.document import Document

from otto.lib.utils import is_reasoning_effort
from otto.llm.utils import DEFAULT_INSTRUCTION

if TYPE_CHECKING:
	from otto.llm.types import ModelSize, Provider, ReasoningEffort


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
		supports_vision: DF.Check
		title: DF.Data
	# end: auto-generated types

	@staticmethod
	def new(
		name: str,
		title: str,
		provider: Provider,
		size: ModelSize,
		is_reasoning: bool = False,
		supports_vision: bool = False,
	):
		doc = cast("OttoLLM", frappe.get_doc({"doctype": "Otto LLM"}))

		doc.name = name
		doc.title = title
		doc.provider = provider
		doc.is_reasoning = is_reasoning
		doc.supports_vision = supports_vision
		doc.size = size

		# Name being present causes doc.save to fail
		doc.insert(ignore_permissions=True)
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
					"stream-llm",
					{
						"llm": self.name,
						"chunk": chunk,
					},
					user=frappe.session.user,
				)
		except Exception as e:
			return {"error": str(e)}

		if stream.failure_reason:
			return {"error": stream.failure_reason}

		if stream.item is None:
			return {
				"message": "success",
			}

		return {
			"message": "success",
			"item": stream.item,
		}


def get_reasoning_effort(effort: str | None, llm: OttoLLM | None = None) -> ReasoningEffort | None:
	if not effort:
		return None

	if (llm and not llm.is_reasoning) or not is_reasoning_effort(effort):
		return None

	return effort
