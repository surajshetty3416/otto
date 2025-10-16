from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
# import frappe
from typing import TYPE_CHECKING, cast

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from jinja2 import Template

if TYPE_CHECKING:
	from otto.lib.types import ReasoningEffort

# TODO:
# - tools
# - re-render instruction on every message
DEFAULT_INSTRUCTION = (
	"You are Otto, a helpful assistant. You are currently speaking to {{user}} and the date is {{date}}."
)


class OttoAssistant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_assistant_tool_ct.otto_assistant_tool_ct import OttoAssistantToolCT

		get_context: DF.Code | None
		instruction: DF.Code | None
		llm: DF.Link | None
		reasoning_effort: DF.Literal["None", "Low", "Medium", "High"]
		title: DF.Data | None
		tools: DF.Table[OttoAssistantToolCT]
	# end: auto-generated types

	@staticmethod
	def new(
		*,
		title: str,
		name: str | None = None,
		llm: str | None = None,
		instruction: str | None = None,
		tools: list[dict] | None = None,
		reasoning_effort: ReasoningEffort | None = None,
	):
		import otto.lib as lib

		doc = cast("OttoAssistant", frappe.new_doc("Otto Assistant"))
		doc.title = title
		doc.llm = llm or lib.get_model(size="Medium")
		doc.instruction = instruction or DEFAULT_INSTRUCTION
		doc.name = name or make_autoname("hash")

		if not reasoning_effort:
			doc.reasoning_effort = "None"
		else:
			doc.reasoning_effort = reasoning_effort

		for tool in tools or []:
			doc.append("tools", tool)

		doc.save()
		return doc

	def before_save(self):
		import otto.lib as lib

		if not self.instruction:
			self.instruction = DEFAULT_INSTRUCTION

		if not self.llm:
			self.llm = lib.get_model(size="Medium")

	@frappe.whitelist()
	def get_instruction(self):
		context = self.run_get_context()
		if not self.instruction:
			return DEFAULT_INSTRUCTION

		template = Template(self.instruction)
		instruction = template.render(context)
		assert isinstance(instruction, str), "type check"
		return instruction

	@frappe.whitelist()
	def run_get_context(self):
		if not self.get_context:
			return {}

		from datetime import datetime

		from otto.utils import execute

		context = execute.execute(
			script=self.get_context,
			args={},
			arg_names=[],
			globals={},
			function_name="get_context",
		)

		user = frappe.session.user
		if full_name := frappe.get_value("User", frappe.session.user, "full_name"):
			user = full_name

		result = context["result"]
		now = datetime.now()
		common = {
			"user": user,
			"date": now.date().isoformat(),
			"time": now.time().isoformat(),
			"datetime": now.isoformat(),
		}

		if not isinstance(result, dict):
			return common

		return {**common, **result}
