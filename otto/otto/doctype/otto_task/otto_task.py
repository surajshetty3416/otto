# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
from typing import Any, cast

import frappe
from frappe.model.document import Document

import otto
from otto.otto.doctype.otto_task.tools import meta_tools

logger = otto.logger("otto_task")

EVENT_MAP = {
	"after_insert": "On Create",
	"on_update": "On Update",
	"on_delete": "On Delete",
	"on_submit": "On Submit",
	"on_cancel": "On Cancel",
	"manual": "Manual",
}


class OttoTask(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from otto.otto.doctype.otto_task_tool_ct.otto_task_tool_ct import OttoTaskToolCT

		event: DF.Literal["On Create", "On Update", "On Delete", "On Submit", "On Cancel", "Manual"]
		get_context: DF.Code | None
		instruction: DF.Code | None
		is_enabled: DF.Check
		llm: DF.Literal["Anthropic Claude Haiku 3.5", "Anthropic Claude Sonnet 3.7", "Anthropic Claude Sonnet 4", "Anthropic Claude Opus 4", "OpenAI o3", "OpenAI o4 mini", "OpenAI GPT-4o", "OpenAI GPT-4o mini", "OpenAI GPT-4.1", "OpenAI GPT-4.1 mini", "OpenAI GPT-4.1 nano"]
		target_doctype: DF.Link
		title: DF.Data | None
		tools: DF.Table[OttoTaskToolCT]
	# end: auto-generated types

	@staticmethod
	def new(target_doctype: str, event: str):
		doc = cast(
			OttoTask,
			frappe.get_doc({"doctype": "Otto Task", "target_doctype": target_doctype, "event": event}),
		)
		doc.save()
		return doc

	@frappe.whitelist()
	def run_task_execution(self, target: str):
		from otto.otto.doctype.otto_execution.otto_execution import OttoExecution

		assert self.name is not None, "type check"
		execution = OttoExecution.new(
			self.name,
			target=target,
			target_doctype=self.target_doctype,
			event="Manual",
		)
		frappe.db.commit()

		frappe.enqueue_doc(
			doctype="Otto Execution",
			name=execution.name,
			method="execute",
			timeout=get_timeout(),
		)
		return execution.name

	@frappe.whitelist()
	def test_get_context(self, target: str):
		from otto.utils.execute import run_get_context

		assert self.get_context is not None, "type check"
		return run_get_context(
			self.get_context,
			doc=frappe.get_doc(self.target_doctype, target),
			event="Manual",
		)

	@frappe.whitelist()
	def list_tools(self):
		assert self.name is not None, "type check"
		return get_tools(self.name)


def handler(name: str, doc: Document, event: str | None = None):
	"""
	Handler function is used to handle the Otto Task.
	"""
	from otto.otto.doctype.otto_execution.otto_execution import OttoExecution

	assert doc.name is not None, "typecheck"
	execution = OttoExecution.new(
		name,
		target=doc.doctype,
		target_doctype=doc.name,
		event=event,
	)
	frappe.db.commit()
	return execution.execute()


def common_handler(doctype: Document, event: str | None = None):
	"""
	Common handler function is used to enqueue tasks for a given doctype and
	event. When an Otto Task is created or updated, the otto.hooks.doc_events is
	updated with for the given doctype and event is updated with this function.
	"""
	if not otto.is_enabled() or not event or event not in EVENT_MAP:
		return

	event_label = EVENT_MAP[event]

	# TODO: Cache this get_all call, update only every 5 minutes or something
	for name in frappe.db.get_all(
		"Otto Task",
		filters={"target_doctype": doctype.doctype, "event": event_label},
		pluck="name",
	):
		logger.info(
			{
				"message": "handler enqueued",
				"otto_task": name,
				"doctype": doctype.doctype,
				"name": doctype.name,
				"event": event,
			}
		)
		frappe.enqueue(
			handler,
			timeout=get_timeout(),
			# Args
			name=name,
			doc=doctype,
			event=event_label,
		)


def get_tools(task: str):
	from otto.otto.doctype.otto_tool.otto_tool import OttoTool

	tools = []
	for tool in frappe.get_all(
		"Otto Task Tool CT",
		filters={"parent": task},
		pluck="tool",
	):
		tool_doc = otto.get(OttoTool, tool)
		print(tool_doc.is_valid, tool_doc.get_function_schema())
		if not tool_doc.is_valid:
			continue

		tools.append(tool_doc.get_function_schema())

	tools.extend(meta_tools)
	return tools


def get_timeout():
	return frappe.get_cached_value("Otto Settings", "Otto Settings", "task_execution_timeout") * 60
