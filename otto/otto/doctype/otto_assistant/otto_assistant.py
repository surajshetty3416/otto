from __future__ import annotations

import re

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
# import frappe
from typing import TYPE_CHECKING, Any, cast

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from jinja2 import Template

from otto.llm.utils import DEFAULT_MODEL
from otto.utils import get_import_path

if TYPE_CHECKING:
	from collections.abc import Callable

	from otto.lib.types import ReasoningEffort

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
		get_context_import_path: DF.Data | None
		instruction: DF.Code
		is_app_defined: DF.Check
		llm: DF.Link
		reasoning_effort: DF.Literal["None", "Low", "Medium", "High"]
		supports_user_directives: DF.Check
		title: DF.Data
		tools: DF.Table[OttoAssistantToolCT]
	# end: auto-generated types

	@staticmethod
	def new(
		*,
		title: str,
		name: str | None = None,
		llm: str | None = None,
		instruction: str | None = None,
		tools: list[str] | None = None,
		reasoning_effort: ReasoningEffort | None = None,
		get_context: str | Callable | None = None,
		is_app_defined: bool = False,
	):
		import otto.lib as lib

		doc = cast("OttoAssistant", frappe.new_doc("Otto Assistant"))
		doc.title = title
		doc.llm = llm or lib.get_model(size="Medium") or DEFAULT_MODEL
		doc.instruction = instruction or DEFAULT_INSTRUCTION
		doc.name = name or f"assistant-{make_autoname('hash')}"
		doc.is_app_defined = is_app_defined

		if not reasoning_effort:
			doc.reasoning_effort = "None"
		else:
			doc.reasoning_effort = reasoning_effort

		doc.set_get_context(get_context)
		if tools:
			doc.set_tools(tools)

		doc.save()
		return doc

	def before_save(self):
		import otto.lib as lib

		if not self.instruction:
			self.instruction = DEFAULT_INSTRUCTION

		if not self.llm:
			self.llm = lib.get_model(size="Medium") or DEFAULT_MODEL

		# Look for a literal `{{ user_directives }}`
		match = re.search(r"\{\{\s*user_directives\s*\}\}", self.instruction)
		self.supports_user_directives = bool(match)

	@frappe.whitelist()
	def get_instruction(self, context: dict | None = None):
		_context = self.run_get_context()
		if not self.instruction:
			return DEFAULT_INSTRUCTION

		template = Template(self.instruction)
		if context:
			_context = {**_context, **context}

		instruction = template.render(_context)
		assert isinstance(instruction, str), "type check"
		return instruction

	@frappe.whitelist()
	def run_get_context(self):
		from datetime import datetime

		user = frappe.session.user
		if full_name := frappe.get_value("User", frappe.session.user, "full_name"):
			user = full_name

		now = datetime.now()
		common = {
			"user": user,
			"date": now.date().isoformat(),
			"time": now.time().isoformat(),
			"datetime": now.isoformat(),
		}

		result = self._run_get_context()
		if not isinstance(result, dict):
			return common

		return {**common, **result}

	def _run_get_context(self) -> Any:
		from otto.utils import execute, import_fn

		if self.get_context_import_path:
			fn = import_fn(self.get_context_import_path)
			return fn()

		if not self.get_context:
			return None

		context = execute.execute(
			script=self.get_context,
			args={},
			arg_names=[],
			globals={},
			function_name="get_context",
		)

		return context["result"]

	def set_get_context(self, get_context: str | Callable | None):
		if callable(get_context):
			self.get_context = None
			self.get_context_import_path = get_import_path(get_context)

		if isinstance(get_context, str):
			self.get_context_import_path = None
			self.get_context = get_context

	def set_tools(self, tools: list[str]):
		self.tools.clear()
		tool_rows = frappe.get_all(
			"Otto Tool",
			filters={"name": ["in", tools]},
			fields=["name", "slug", "requires_permission"],
		)
		tool_map = {row["name"]: row for row in tool_rows}
		for tool in tools:
			src = tool_map.get(tool)
			if not src:
				continue

			self.append(
				"tools",
				{
					"tool": tool,
					"slug": src.get("slug"),
					"is_enabled": True,
					"requires_permission": src.get("requires_permission", False),
				},
			)
