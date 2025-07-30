# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Literal, cast

import frappe
from frappe.model.document import Document

import otto
from otto import llm
from otto.llm.types import Content, ToolUseUpdate
from otto.otto.doctype.otto_task.tools import is_meta_tool

if TYPE_CHECKING:
	from otto.llm.types import SessionItem
	from otto.otto.doctype.otto_session.otto_session import OttoSession

logger = otto.logger("otto_execution")
DEFAULT_MAX_LLM_CALLS = 30


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

	def before_save(self):
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
			self.set_status("Failure", "\n".join(reasons), skip_save=True)

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
			self.run_tools(session)
		except Exception as e:
			otto.log_error(title="run_tools error", doc=self)
			return self.set_status("Failure", f"Error in run_tools: {e}")

		if self.should_stop(session):
			return self.set_status("Success")

		self.loop(None)

	def run_tools(self, session_doc: OttoSession):
		"""Executes tool use requests from the last LLM response.

		This method inspects the last `SessionItem`. If it contains `tool_use`
		content, it executes the requested tools and appends the results to the
		session. It also handles special meta tools, like `end_task`.
		"""
		from otto.otto.doctype.otto_session.otto_session import get_tool_map

		item = session_doc.get_last_item()
		if item is None:
			return

		session = session_doc._get_session()
		if session is None:
			return

		env_map = {t.name: t.env for t in session_doc.tools}
		tool_map = get_tool_map(session_doc.tools)

		# Move meta tools to the end of the list
		content = sorted(item["content"], key=lambda x: is_meta_tool(x))

		for content in item["content"]:
			if content["type"] != "tool_use":
				continue

			# Used if meta tool
			update = ToolUseUpdate(
				start_time=time.time(),
				end_time=time.time(),
				is_error=False,
				result="",
				stdout=None,
				stderr=None,
			)

			if not is_meta_tool(content):
				tool_name = tool_map[content["name"]]
				env_str = env_map.get(tool_name, None)
				update = self._execute_tool(tool_name, content["args"], env_str)

			llm.update_with_tool_result(session=session, id=content["id"], update=update)
			session_doc._set_session(session)

	def _execute_tool(self, tool_name: str, args: dict, env_str: str | None) -> ToolUseUpdate:
		"""Executes tool and returns tuple of (result, is_error)"""
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		tool_doc = otto.get(OttoTool, tool_name)
		update = ToolUseUpdate(
			start_time=time.time(),
			end_time=time.time(),
			is_error=False,
			result="",
			stdout=None,
			stderr=None,
		)

		try:
			env = json.loads(env_str) if env_str else None
			result = tool_doc.execute(
				args,
				task=self.task,
				session=self.session,
				env=env,
			)
			update["is_error"] = False
			update["result"] = result["result"]
			update["stdout"] = result["stdout"]
			update["stderr"] = result["stderr"]
			update["end_time"] = time.time()
		except Exception as e:
			otto.log_error(
				"Tool Use Error",
				doc=self,
				tool=tool_name,
			)
			update["is_error"] = True
			update["result"] = str(e)
			update["end_time"] = time.time()
		return update

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
		skip_save: bool = False,  # used in before save to prevent recursion
	):
		self.status = status
		self.reason = reason

		if skip_save:
			return

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
			doctype="Otto Execution",
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
