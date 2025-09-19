# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Literal, cast

import frappe
from frappe.model.document import Document

import otto
from otto.llm.types import ReasoningEffort, ToolUseUpdate
from otto.otto.doctype.otto_task.tools import is_meta_tool
from otto.utils.lock import lock_doc

logger = otto.logger("otto.doctype.otto_execution")
DEFAULT_MAX_LLM_CALLS = 30

if TYPE_CHECKING:
	from otto.lib import Session


class OttoExecution(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		event: DF.Data | None
		reason: DF.SmallText | None
		session: DF.Link
		status: DF.Literal["Pending", "Waiting", "Running", "Success", "Failure"]
		target: DF.DynamicLink | None
		target_doctype: DF.Link | None
		task: DF.Link
	# end: auto-generated types

	_session: Session | None = None

	@staticmethod
	def new(
		task: str,
		*,
		target: str | None,
		target_doctype: str | None,
		event: str | None = None,
		llm: str | None = None,
		reasoning_effort: ReasoningEffort | None = None,
		instruction: str | None = None,
	):
		import otto.lib as lib
		from otto.otto.doctype.otto_task.otto_task import get_tools

		doc = cast("OttoExecution", frappe.get_doc({"doctype": "Otto Execution", "task": task}))

		doc.target_doctype = target_doctype
		doc.target = target
		doc.event = event

		if reasoning_effort is None:
			reasoning_effort = frappe.get_cached_value("Otto Task", task, "reasoning_effort")

		session = lib.new(
			model=llm or frappe.get_cached_value("Otto Task", task, "llm"),
			instruction=instruction or frappe.get_cached_value("Otto Task", task, "instruction"),
			reasoning_effort=reasoning_effort,
			tools=get_tools(task),
		)

		doc.session = session.id
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
		session = self.get_session()

		try:
			item, reason = session.interact(context, stream=False)
		except Exception as e:
			otto.log_error(title="interact error", doc=self)
			return self.set_status("Failure", f"Interaction errored out: {e}")

		if reason:
			return self.set_status("Failure", reason)

		if item is None:
			return self.set_status("Failure", reason)

		return self._run_tools_and_loop(session)

	def _run_tools_and_loop(self, session: Session):
		set_waiting = False
		try:
			set_waiting = self._run_tools(session)
		except Exception as e:
			otto.log_error(title="run_tools error", doc=self)
			return self.set_status("Failure", f"Error in run_tools: {e}")

		if set_waiting:
			return self.set_status("Waiting")

		if self.should_stop(session):
			return self.set_status("Success")

		return self.loop(None)

	def resume(self):
		"""
		Resume is invoked after a permission is granted or denied.

		Multiple permissions can be acknowledged at once for a single execution,
		lock is used to ensure that only one of the multiple calls runs.
		"""
		with lock_doc(self, lock_name="waiting_check"):
			if self.status != "Waiting":
				return
			self.set_status("Running")

		session = self.get_session()
		self._run_tools_and_loop(session)

	def _run_tools(self, session: Session) -> bool:
		"""Executes tool use requests from the last LLM response.

		This method inspects the last `SessionItem`. If it contains `tool_use`
		content, it executes the requested tools and appends the results to the
		session. It also handles special meta tools, like `end_task`.
		"""
		from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest
		from otto.otto.doctype.otto_task.otto_task import get_tool_map
		from otto.utils.notify import PermissionRequest

		if not (pending := session.get_pending_tool_use()):
			return False

		set_waiting = False
		updates: list[ToolUseUpdate] = []
		tool_map = get_tool_map(self.task)
		permission_map = self.get_permission_map()
		new_perms: list[PermissionRequest] = []

		for tool in pending:
			tool_name, env_str, requires_permission = tool_map.get(tool.name, (None, None, False))

			if requires_permission and tool.id not in permission_map:
				assert self.name is not None, "type check"
				permission = OttoPermissionRequest.new(session=self.session, tool_use_id=tool.id)

				assert permission.name is not None, "type check"
				new_perms.append(
					PermissionRequest(
						# Context
						task=self.task,
						permission=permission.name,
						execution=self.name,
						session=self.session,
						# Target
						target=self.target,
						target_doctype=self.target_doctype,
						# Tool
						tool=tool_name,
						tool_use_id=tool.id,
						tool_slug=tool.name,
						tool_args=tool.args,
					)
				)

			if requires_permission and permission_map.get(tool.id, "Pending") == "Pending":
				set_waiting = True
				continue

			permission_granted = True
			if requires_permission:
				permission_granted = permission_map.get(tool.id, "Pending") == "Granted"

			update = ToolUseUpdate(id=tool.id)  # Used if meta tool
			if not is_meta_tool(tool.name):
				assert tool_name is not None, "sanity check"
				update = self._execute_tool(
					tool_name=tool_name,
					args=tool.args,
					tool_use_id=tool.id,
					env_str=env_str,
					permission_granted=permission_granted,
				)

			updates.append(update)

		session.update_tool_use(updates)

		if new_perms:
			self.get_assigned_users()
			frappe.enqueue(
				method="otto.utils.notify.notify",
				perms=new_perms,
			)

		return set_waiting

	def _execute_tool(
		self,
		*,
		tool_name: str,
		args: dict,
		tool_use_id: str,
		env_str: str | None,
		permission_granted: bool,
	) -> ToolUseUpdate:
		"""Executes tool and returns tuple of (result, is_error)"""
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		update = ToolUseUpdate(id=tool_use_id, start_time=time.time(), end_time=time.time())
		if not permission_granted:
			update["is_error"] = True
			update["result"] = "Permission to use tool denied by user"
			return update

		tool_doc = otto.get(OttoTool, tool_name)
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
		except Exception as e:
			otto.log_error(
				"Tool Use Error",
				doc=self,
				tool=tool_name,
			)
			update["is_error"] = True
			update["result"] = str(e)
		finally:
			update["end_time"] = time.time()
		return update

	def should_stop(self, session: Session) -> bool:
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

		if max_llm_calls > 0 and session.get_llm_call_count() >= max_llm_calls:
			self.set_status("Failure", "Max LLM calls reached")
			return True

		# This has been added cause Gemini 2.5 Flash did not call end_task and
		# instead so for smaller models, this check should suffice until a better
		# solution is found.
		if item["meta"]["output_tokens"] == 0:
			self.set_status("Failure", "No output tokens")
			return True

		return False

	def get_session(self) -> Session:
		import otto.lib as lib

		if self._session is not None:
			return self._session

		return lib.load(self.session)

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
		status: Literal["Pending", "Waiting", "Running", "Success", "Failure"],
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
	def get_permission_map(self, only_pending: bool = False) -> dict[str, str]:
		"""Returns a map of tool use IDs to their status."""
		filters = {"session": self.session}

		if only_pending:
			filters["status"] = "Pending"

		permissions = frappe.get_all(
			"Otto Permission Request",
			filters=filters,
			fields=["tool_use_id", "status"],
		)

		return {p["tool_use_id"]: p["status"] for p in permissions}

	@frappe.whitelist()
	def retry(self):
		import otto.lib as lib
		from otto.otto.doctype.otto_task.otto_task import get_timeout, get_tools

		if self.status != "Failure":
			return "Retry available only for failed sessions"

		prev = self.get_session()
		session = lib.new(
			model=prev.model,
			instruction=prev.instruction,
			reasoning_effort=prev.reasoning_effort,
			tools=get_tools(self.task),
		)

		self.session = session.id
		self.save(ignore_permissions=True, ignore_version=True)

		frappe.enqueue_doc(
			doctype="Otto Execution",
			name=self.name,
			method="execute",
			timeout=get_timeout(),
		)

		return session.id

	@frappe.whitelist()
	def enqueue_resume(self):
		from otto.otto.doctype.otto_task.otto_task import get_timeout

		frappe.enqueue_doc(
			doctype="Otto Execution",
			name=self.name,
			method="resume",
			timeout=get_timeout(),
		)


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
