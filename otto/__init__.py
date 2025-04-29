from __future__ import annotations

from typing import TYPE_CHECKING

__version__ = "0.0.1"

import frappe
import frappe.utils.logger

if TYPE_CHECKING:
	from frappe.model.document import Document


def logger(name: str | Document):
	frappe.utils.logger.set_log_level("INFO")
	if not isinstance(name, str):
		doc = name
		name = doc.doctype.lower().replace(" ", ".")

		if doc.name:
			name += ":" + doc.name

	return frappe.logger(name)


__all__ = ["logger"]
