# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

import json
from typing import Any

import frappe
from frappe.model.document import Document

from otto.otto.doctype.otto_task.utils import logger, update_doc_events


class OttoTask(Document):
	pass


def handler(doctype: str, event: str):
	# Given to otto.hooks.doc_events
	logger("otto.task").info(dict(doctype=doctype, event=event))
