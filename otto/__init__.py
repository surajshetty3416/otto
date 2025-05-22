from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Any

__version__ = "0.0.1"
__all__ = ["get", "logger", "log_error"]

from typing import TypeVar, cast

import frappe
import frappe.utils.logger
from frappe.model.document import Document

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


def log_error(
	title: str,
	*,
	doc: Document | None = None,
	**context,
):
	if not title:
		title = "Unknown Error"

	title_prefix = "[Flow]"
	if not title.startswith(title_prefix):
		title = f"{title_prefix} {title}"

	message: dict[str, Any] = dict(
		context=context,
	)

	with contextlib.suppress(Exception):
		context["user"] = frappe.session.user

		if traceback := frappe.get_traceback(with_context=True):
			message["traceback"] = traceback

		frappe.log_error(
			title=title,
			message=json.dumps(
				message,
				indent=4,
				default=str,
				skipkeys=True,
			),
			reference_doctype=doc.doctype if doc else None,
			reference_name=doc.name if doc else None,
		)


classname_doctype_map: dict[str, str] = {}

D = TypeVar("D", bound=Document)


def get(Doc: type[D], name: str, *, cached: bool = False) -> D:
	"""
	Custom `get_doc` implementation for flow. Invocation uses class instead of doctype.

	This allows static type checking without having to manually cast to the
	specific document type.

	Example:
	```
	doc = get(FLScriptTask, task_name)
	```
	"""

	doctype = get_doctype_name(Doc)

	# Prevent frappe.db.get_value call in when calling frappe.get_doc
	site_controllers = cast(
		"dict[str, dict[str, Document]]",
		frappe.controllers,
	).setdefault(frappe.local.site, {})
	if doctype not in site_controllers:
		site_controllers[doctype] = cast("Document", Doc)

	if cached:
		return cast("D", frappe.get_cached_doc(doctype, name))

	return cast("D", frappe.get_doc(doctype, name))


def get_doctype_name(doc: type[D]) -> str:
	classname = doc.__name__
	if classname in classname_doctype_map:
		return classname_doctype_map[classname]

	for doctype in cast("list[str]", frappe.get_all("DocType", pluck="name")):
		classname_doctype_map[doctype.replace(" ", "").replace("-", "")] = doctype

	return classname_doctype_map[classname]
