from __future__ import annotations

import frappe

from otto.utils import json_dumps

"""
Code in this is passed as library code to tool execution as globals.
"""

from typing import Any


def log(
	content: Any,
	*,
	tool: str | None = None,
	task: str | None = None,
	execution: str | None = None,
):
	"""Creates a new scrapbook entry"""

	from otto.otto.doctype.otto_scrapbook.otto_scrapbook import OttoScrapbook

	if not isinstance(content, str):
		content = json_dumps(content)

	OttoScrapbook.new(content, tool=tool, task=task, execution=execution)


def get_lib():
	return frappe._dict({"log": log})
