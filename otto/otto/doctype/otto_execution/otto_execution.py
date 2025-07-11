# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, cast

import frappe
from frappe.model.document import Document

import otto
from otto.llm.types import Content

if TYPE_CHECKING:
	from otto.llm.types import SessionItem
	from otto.otto.doctype.otto_session.otto_session import OttoSession

logger = otto.logger("otto_execution")
DEFAULT_MAX_LLM_CALLS = 10


class OttoExecution(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		event: DF.Data | None
		reason: DF.SmallText | None
		session: DF.Link
		status: DF.Literal["Pending", "Running", "Success", "Failure"]
		target: DF.DynamicLink | None
		target_doctype: DF.Link | None
		task: DF.Link
	# end: auto-generated types
	_session: OttoSession | None = None

	@staticmethod
	def new(
		task: str,
		*,
		target: str | None,
		target_doctype: str | None,
		event: str | None = None,
		llm: str | None = None,
		reasoning_effort: str | None = None,
		instruction: str | None = None,
	):
		from otto.otto.doctype.otto_session.otto_session import OttoSession

		doc = cast(OttoExecution, frappe.get_doc({"doctype": "Otto Execution", "task": task}))

		doc.target_doctype = target_doctype
		doc.target = target
		doc.event = event

		if reasoning_effort and reasoning_effort in ["None", "Low", "Medium", "High"]:
			reasoning_effort = reasoning_effort  # type: ignore
		else:
			reasoning_effort = frappe.get_cached_value("Otto Task", task, "reasoning_effort")

		session = OttoSession.new(
			llm=llm or frappe.get_cached_value("Otto Task", task, "llm"),
			instruction=instruction or frappe.get_cached_value("Otto Task", task, "instruction"),
			reasoning_effort=reasoning_effort,
			session_type="Task",
		)
		set_session_tools(session, task)

		assert session.name is not None, "type check"
		doc.session = session.name
		doc.save(ignore_permissions=True, ignore_version=True)
		return doc

	def execute(self):
		self.set_status("Running")
		doc = self.get_target()
		context, reason = self.get_context(doc, self.event or "Manual")

		if not context:
			return self.set_status("Failure", reason)

		try:
			self.loop(context)
		except Exception as e:
			otto.log_error(title="execute error", doc=self)
			self.set_status("Failure", f"Error in session loop: {e}")

	def get_target(self):
		if not self.target_doctype or not self.target:
			return None

		return frappe.get_doc(self.target_doctype, self.target)

	def validate(self):
		tool_names = frappe.get_all("Otto Task Tool CT", filters={"parent": self.task}, pluck="tool")
		tools = frappe.get_all("Otto Tool", filters={"name": ("in", tool_names)}, fields=["slug", "is_valid"])

		reasons = []

		for tool in tools:
			if not tool.is_valid:
				reasons.append(f"Tool {tool.slug} is not valid")

			if not tool.env:
				continue

			try:
				json.loads(tool.env)
			except Exception as e:
				reasons.append(f"Tool {tool.slug} env is not valid JSON: {e}")

		if reasons:
			self.set_status("Failure", "\n".join(reasons))

	def loop(self, context: str | list[str] | None = None):
		try:
			session = self.get_session()
			item, reason = session.interact(context)
		except Exception as e:
			otto.log_error(title="interact error", doc=self)
			return self.set_status("Failure", f"Interaction errored out: {e}")

		if reason:
			return self.set_status("Failure", reason)

		if item is None:
			return self.set_status("Failure", reason)

		try:
			session.run_tools()
		except Exception as e:
			otto.log_error(title="run_tools error", doc=self)
			return self.set_status("Failure", f"Error in run_tools: {e}")

		if self.should_stop(session):
			return self.set_status("Success")

		self.loop(None)

	def should_stop(self, session: OttoSession) -> bool:
		item = session.get_last_item()
		if item is None:
			return False

		"""Check if end_task has been called or if session is looping indefinitely."""
		for c in item["content"]:
			if c["type"] == "tool_use" and c["name"] == "end_task":
				self.set_status("Success")
				return True

		max_llm_calls = frappe.get_cached_value(
			"Otto Settings",
			"Otto Settings",
			"max_llm_calls",
		)
		if max_llm_calls is None:
			max_llm_calls = DEFAULT_MAX_LLM_CALLS

		if max_llm_calls > 0 and session.get_count_of_llm_calls() >= max_llm_calls:
			self.set_status("Failure", "Max LLM calls reached")
			return True

		# This has been added cause Gemini 2.5 Flash did not call end_task and
		# instead so for smaller models, this check should suffice until a better
		# solution is found.
		if item["meta"]["output_tokens"] == 0:
			self.set_status("Failure", "No output tokens")
			return True

		return False

	def get_session(self) -> OttoSession:
		from otto.otto.doctype.otto_session.otto_session import OttoSession

		if self._session is not None:
			return self._session

		self._session = otto.get(OttoSession, self.session)
		return self._session

	def get_context(self, doc: Document | None, event: str) -> tuple[str | list, None] | tuple[None, str]:
		from otto.otto.doctype.otto_task.otto_task import run_get_context

		get_context = frappe.get_value("Otto Task", self.task, "get_context")
		if (not get_context or not isinstance(get_context, str)) and doc:
			return doc.as_json(), None

		if not isinstance(get_context, str) or not get_context:
			return (None, "get_context is not set on Task and no target Doc is provided")

		try:
			context = run_get_context(get_context, doc, event)
		except Exception as e:
			otto.log_error(title="get_context error", doc=self)
			return None, str(e)

		return context, None

	def set_status(
		self,
		status: Literal["Pending", "Running", "Success", "Failure"],
		reason: str | None = None,
	):
		self.status = status
		self.reason = reason
		self.save(ignore_permissions=True, ignore_version=True)
		frappe.db.commit()

	@frappe.whitelist()
	def retry(self):
		if self.status != "Failure":
			return "Retry available only for failed sessions"
		from otto.otto.doctype.otto_task.otto_task import get_timeout

		self.set_status("Running")
		self.save()

		frappe.enqueue_doc(
			doctype="Otto Session",
			name=self.name,
			method="loop",
			timeout=get_timeout(),
		)

		return "Session enqueued"


@frappe.whitelist()
def get_recent_execution(limit: int = 20) -> list[dict]:
	sessions = frappe.get_all(
		"Otto Execution",
		fields=["name", "status", "creation", "task", "target", "target_doctype"],
		limit=limit,
		order_by="modified desc",
	)
	tasks = frappe.get_all(
		"Otto Task", filters={"name": ("in", [e["task"] for e in sessions])}, fields=["name", "title"]
	)
	task_map = {t["name"]: t for t in tasks}

	for session in sessions:
		session["task_name"] = task_map[session["task"]]["title"]

	return sessions


@frappe.whitelist()
def get_adjacent_execution(name: str, next: str | bool):
	if isinstance(next, str):
		"""frappe.call appears to be sending a string instead of a boolean, wt"""
		next = next == "true"

	"""Get the next or previous session in chronological order"""
	order = "asc" if next else "desc"
	operator = ">" if next else "<"

	session = frappe.get_all(
		"Otto Execution",
		filters={
			"modified": (operator, frappe.get_value("Otto Execution", name, "modified")),
		},
		order_by=f"modified {order}",
		limit=1,
		pluck="name",
	)

	if session:
		return session[0]

	return None


def set_session_tools(session: OttoSession, task: str):
	tools = frappe.get_all(
		"Otto Task Tool CT",
		filters={"parent": task, "is_enabled": True},
		fields=["tool", "slug", "env"],
	)
	for t in tools:
		session.append("tools", {**t, "is_enabled": True})

	session.save(ignore_permissions=True, ignore_version=True)
	frappe.db.commit()
