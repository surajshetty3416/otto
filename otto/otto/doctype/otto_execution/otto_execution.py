# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

# import frappe
import json
from typing import TYPE_CHECKING, Literal, cast

import frappe
from frappe.model.document import Document

import otto
from otto import llm
from otto.otto.doctype.otto_execution.execute import run_get_context
from otto.otto.doctype.otto_task.otto_task import get_tools

if TYPE_CHECKING:
	from otto.llm.types import ExchangeItem


class OttoExecution(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		execution: DF.JSON | None
		reason: DF.SmallText | None
		status: DF.Literal["Pending", "Running", "Success", "Failure"]
		task: DF.Link
	# end: auto-generated types

	@staticmethod
	def new(task: str):
		doc = cast(OttoExecution, frappe.get_doc({"doctype": "Otto Execution", "task": task}))
		doc.save()
		return doc

	def execute(self, doc: Document, event: str | None = None):
		otto.logger(self).info(
			{
				"message": "execute called",
				"name": self.name,
				"task": self.task,
			}
		)
		self.set_status("Running")
		if not (context := self.get_context(doc, event)):
			return

		otto.logger(self).info(
			{
				"message": "system rendered",
				"name": self.name,
				"context": context,
			}
		)
		self.loop(context)

	def loop(self, context: str | list[str] | None = None):
		exchange = json.loads(self.execution) if self.execution else None
		try:
			interaction, reason = llm.interact(
				context,  # type: ignore needed cause not strong enough type system
				exchange=exchange,
				tools=get_tools(self.task),
				model="claude-3-7-sonnet-latest",
				system=self.get_instruction(),
			)
		except Exception as e:
			otto.logger(self).error(
				{
					"message": "interact error",
					"name": self.name,
					"error": e,
				}
			)
			self.set_status("Failure", f"Interaction errored out: {e}")
			return

		if interaction is None:
			self.set_status("Failure", reason)
			return

		execution = interaction["update"]
		self.execution = json.dumps(execution, indent=2)
		self.save()

		item = interaction["item"]
		if item["meta"]["end_reason"] == "turn_end":
			self.set_status("Success")
			return

		self.run_tool(item)
		self.loop(None)

	def run_tool(self, item: ExchangeItem):
		# TODO: run tool, and update exchange
		pass

	def get_instruction(self):
		instruction = frappe.get_cached_value("Otto Task", self.task, "instruction")
		assert isinstance(instruction, str), "typecheck"
		return instruction

	def get_context(self, doc: Document, event: str | None = None):
		get_context = frappe.get_value("Otto Task", self.task, "get_context")
		if not get_context or not isinstance(get_context, str):
			return doc.as_json()

		try:
			context = run_get_context(get_context, doc, event)
		except Exception as e:
			otto.logger(self).error(
				{
					"message": "set_context error",
					"name": self.name,
					"error": e,
				}
			)
			self.set_status("Failure", str(e))
			return None

		return context

	def set_status(
		self,
		status: Literal["Pending", "Running", "Success", "Failure"],
		reason: str | None = None,
	):
		self.status = status
		self.reason = reason
		self.save()
