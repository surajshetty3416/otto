# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
from typing import Any, cast

import frappe
from frappe.model.document import Document

import otto
from otto.otto.doctype.otto_task.tools import meta_tools

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
		target: DF.Link
		title: DF.Data | None
		tools: DF.Table[OttoTaskToolCT]
	# end: auto-generated types

	@staticmethod
	def new(target: str, event: str):
		doc = cast(OttoTask, frappe.get_doc({"doctype": "Otto Task", "target": target, "event": event}))
		doc.save()
		return doc

	@frappe.whitelist()
	def handle(self, target_doctype: Document):
		# Used to test from the Task doc's desk formview.
		assert self.name is not None, "type check"
		otto.logger(self).info(
			{
				"message": "handle called",
				"doctype": target_doctype.doctype,
				"name": target_doctype.name,
				"event": "Manual",
			}
		)

		frappe.enqueue(
			handler,
			queue="default",
			name=self.name,
			target_doctype=target_doctype,
			target_event="Manual",
		)

	@frappe.whitelist()
	def run(self, target_doctype: Document):
		from otto.otto.doctype.otto_execution.otto_execution import OttoExecution

		assert self.name is not None, "type check"
		return OttoExecution.new(self.name).execute(target_doctype, "Manual")


def handler(name: str, target_doctype: Document, target_event: str | None = None):
	"""
	Handler function is used to handle the Otto Task.
	"""
	from otto.otto.doctype.otto_execution.otto_execution import OttoExecution

	return OttoExecution.new(name).execute(target_doctype, target_event)


def common_handler(doctype: Document, event: str | None = None):
	"""
	Common handler function is used to enqueue tasks for a given doctype and
	event. When an Otto Task is created or updated, the otto.hooks.doc_events is
	updated with for the given doctype and event is updated with this function.
	"""
	if not event or event not in EVENT_MAP:
		return

	event_label = EVENT_MAP[event]

	# TODO: Cache this get_all call, update only every 5 minutes or something
	for name in frappe.db.get_all(
		"Otto Task",
		filters={"target": doctype.doctype, "event": event_label},
		pluck="name",
	):
		otto.logger("otto.task").info(
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
			queue="default",
			name=name,
			target_doctype=doctype,
			target_event=event_label,
		)


def get_tools(task: str):
	from otto.otto.doctype.otto_tool.otto_tool import OttoTool

	tools = frappe.get_all(
		"Otto Task Tool",
		filters={"parent": task},
		pluck="tool",
	)

	tools = []
	for tool in tools:
		tool_doc = otto.get(OttoTool, tool)
		if not tool_doc.is_valid:
			continue

		tools.append(tool_doc.get_function_schema())

	tools.extend(meta_tools)
	return tools
