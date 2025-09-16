# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

import json
from typing import Literal, cast

import frappe
from frappe.model.document import Document

from otto.lib.types import ToolUseContent
from otto.lib.utils import get_tool_use


class OttoPermissionRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		session: DF.Link
		status: DF.Literal["Pending", "Granted", "Denied"]
		tool_use_id: DF.Data
	# end: auto-generated types

	_tool: dict[str, str] | None = None
	_execution: dict[str, str] | None = None
	_tool_use: ToolUseContent | None = None

	@property
	def execution_(self) -> dict[str, str]:
		if not self._execution:
			execs = frappe.get_list(
				"Otto Execution",
				filters={"session": self.session},
				fields=["name", "task", "target", "target_doctype"],
				limit=1,
			)
			self._execution = execs[0] if execs else None

		return self._execution or {}

	@property
	def tool_(self) -> dict[str, str]:
		from otto.otto.doctype.otto_task.otto_task import get_tool_name

		if self._tool:
			return self._tool

		if not self.tool_use_ or not self.task:
			return {}

		tool_name = get_tool_name(self.task, self.tool_use_["name"])
		if not tool_name:
			return {}

		tool = frappe.get_all(
			"Otto Tool",
			filters={"name": tool_name},
			fields=["name", "slug", "title"],
			limit=1,
		)

		if tool:
			self._tool = tool[0]

		return self._tool or {}

	@property
	def tool_use_(self) -> ToolUseContent | None:
		if self._tool_use is None:
			self._tool_use = get_tool_use(self.session, self.tool_use_id)
		return self._tool_use

	@property
	def execution(self) -> str | None:
		return self.execution_.get("name")

	@property
	def task(self) -> str | None:
		return self.execution_.get("task")

	@property
	def target(self) -> str | None:
		return self.execution_.get("target")

	@property
	def target_doctype(self) -> str | None:
		return self.execution_.get("target_doctype")

	@property
	def tool_status(self):
		if not self.tool_use_:
			return "unknown"

		return self.tool_use_["status"]

	@property
	def tool_name(self) -> str | None:
		return self.tool_.get("name")

	@property
	def tool_slug(self) -> str:
		if not self.tool_use_:
			return "unknown"

		return self.tool_use_["name"]

	@property
	def tool_use_args(self) -> str:
		if not self.tool_use_:
			return "{}"

		return json.dumps(self.tool_use_["args"], indent=2)

	@property
	def tool_use_result(self) -> str | None:
		if not self.tool_use_:
			return None

		return self.tool_use_["result"]

	@staticmethod
	def new(
		*,
		session: str,
		tool_use_id: str,
	):
		doc = cast("OttoPermissionRequest", frappe.get_doc({"doctype": "Otto Permission Request"}))
		doc.session = session
		doc.tool_use_id = tool_use_id
		doc.status = "Pending"
		doc.save(ignore_permissions=True, ignore_version=True)
		return doc

	@frappe.whitelist()
	def grant(self):
		self.acknowledge("Granted")

	@frappe.whitelist()
	def deny(self):
		self.acknowledge("Denied")

	def acknowledge(self, status: Literal["Granted", "Denied"]):
		if self.status != "Pending":
			return

		self.set_status(status)
		self.resume()

	def set_status(self, status: Literal["Granted", "Denied"]):
		self.status = status
		self.save()

	def resume(self):
		from otto.otto.doctype.otto_task.otto_task import get_timeout

		execs = frappe.db.get_list(
			"Otto Execution",
			filters={"session": self.session},
			fields=["name"],
			limit=1,
			pluck="name",
		)
		if not execs:
			return

		frappe.enqueue_doc(
			doctype="Otto Execution",
			name=execs[0],
			method="resume",
			timeout=get_timeout(),
		)
