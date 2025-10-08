# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, cast

import frappe
from frappe.model.document import Document

from otto.lib.utils import get_tool_use

if TYPE_CHECKING:
	from otto.lib.types import ToolUseContent


class OttoPermissionRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		args_updated: DF.Check
		session: DF.Link
		status: DF.Literal["Pending", "Granted", "Denied"]
		tool_use_id: DF.Data
	# end: auto-generated types

	_descriptions: dict[str, str] | None = None
	_tool: dict[str, str] | None = None
	_execution: dict[str, str] | None = None
	_tool_use: ToolUseContent | None = None

	@property
	def execution_(self) -> dict[str, str]:
		if not self._execution:
			execs = frappe.get_all(
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
	def descriptions(self) -> dict[str, str]:
		if not self.tool_name:
			return {}

		if self._descriptions:
			return self._descriptions

		desc = frappe.get_all(
			"Otto Tool Arg CT",
			filters={"parent": self.tool_name},
			fields=["arg_name", "description"],
		)
		self._descriptions = {d.arg_name: d.description for d in desc}
		return self._descriptions

	@property
	def tool_use_(self) -> ToolUseContent | None:
		if self._tool_use is None:
			self._tool_use = get_tool_use(self.session, self.tool_use_id)
		return self._tool_use

	@property
	def execution(self) -> DF.Link | None:
		return self.execution_.get("name")

	@property
	def task(self) -> DF.Link | None:
		return self.execution_.get("task")

	@property
	def target(self) -> DF.DynamicLink | None:
		return self.execution_.get("target")

	@property
	def target_doctype(self) -> DF.Link | None:
		return self.execution_.get("target_doctype")

	@property
	def tool_status(self):
		if not self.tool_use_:
			return "unknown"

		return self.tool_use_["status"]

	@property
	def tool_name(self) -> DF.Link | None:
		return self.tool_.get("name")

	@property
	def tool_slug(self) -> str:
		if not self.tool_use_:
			return "unknown"

		return self.tool_use_["name"]

	@property
	def tool_use_args(self) -> DF.Code | None:
		if not self.tool_use_:
			return "{}"

		args = self.tool_use_["args"]
		if self.tool_use_["override"]:
			args = {**args, **self.tool_use_["override"]}

		return json.dumps(args, indent=2)

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
	def grant(self, override_args: dict | None = None):
		return self.acknowledge("Granted", override_args)

	@frappe.whitelist()
	def deny(self):
		return self.acknowledge("Denied")

	def acknowledge(
		self,
		status: Literal["Granted", "Denied"],
		override_args: dict | None = None,
	):
		if self.status != "Pending":
			return {"message": "Request already acknowledged"}

		if override_args and status == "Granted":
			set_override(self.session, self.tool_use_id, override_args)
			self.args_updated = True

		self.set_status(status)
		self.resume()
		return {"message": f"Request {status.lower()}"}

	def set_status(self, status: Literal["Granted", "Denied"]):
		self.status = status
		self.save()

	def resume(self):
		from otto.otto.doctype.otto_task.otto_task import get_timeout

		execs = frappe.get_all(
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
			enqueue_after_commit=True,
		)


def set_override(session: str, tool_use_id: str, override_args: dict):
	items = frappe.get_all(
		"Otto Session Item CT",
		filters={"parent": session, "role": "agent"},
		fields=["name", "content"],
	)

	for item in items:
		content = json.loads(item["content"])

		for content_item in content:
			if content_item["type"] != "tool_use" or content_item["id"] != tool_use_id:
				continue

			content_item["override"] = override_args
			frappe.db.set_value(
				"Otto Session Item CT",
				item["name"],
				"content",
				json.dumps(content),
			)
			break
