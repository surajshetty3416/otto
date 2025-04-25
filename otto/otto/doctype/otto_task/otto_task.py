# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
from typing import Any, cast

import frappe
from frappe.model.document import Document

from otto.otto.doctype.otto_task.utils import logger

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

		event: DF.Literal["On Create", "On Update", "On Delete", "On Submit", "On Cancel"]
		get_context: DF.Code | None
		instruction: DF.Code | None
		is_enabled: DF.Check
		target: DF.Link
		title: DF.Data | None
	# end: auto-generated types

	@staticmethod
	def new(target: str, event: str):
		doc = cast(OttoTask, frappe.get_doc({"doctype": "Otto Task", "target": target, "event": event}))
		doc.save()
		return doc

	def handler(self, target_doctype: Document, target_event: str | None = None):
		target_event = target_event or "Manual"
		logger("otto.task").info(
			{
				"message": "handler called",
				"doctype": target_doctype.doctype,
				"name": target_doctype.name,
				"event": target_event,
			}
		)


def handler(name: str, target_doctype: Document, target_event: str | None = None):
	"""
	Handler function is used to handle the Otto Task.
	"""
	doc = cast(OttoTask, frappe.get_doc("Otto Task", name))
	doc.handler(target_doctype, target_event)


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
		logger("otto.task").info(
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
