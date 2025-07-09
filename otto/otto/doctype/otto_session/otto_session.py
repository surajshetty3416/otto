# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

# import frappe
import functools
import json
from typing import TYPE_CHECKING, Any, Literal, cast

import frappe
from frappe.model.document import Document

import otto
from otto import llm
from otto.llm.types import ToolUseContent
from otto.otto.doctype.otto_task.otto_task import get_tools
from otto.otto.doctype.otto_task.tools import has_task_ended, is_meta_tool

if TYPE_CHECKING:
	from otto.llm.types import Session, SessionItem
	from otto.otto.doctype.otto_task.otto_task import OttoTask

logger = otto.logger("otto_session")


class OttoSession(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_session_item_ct.otto_session_item_ct import OttoSessionItemCT

		event: DF.Data | None
		instruction: DF.Code | None
		items: DF.Table[OttoSessionItemCT]
		llm: DF.Link | None
		reason: DF.SmallText | None
		reasoning_effort: DF.Literal["None", "Low", "Medium", "High"]
		status: DF.Literal["Pending", "Running", "Success", "Failure"]
		target: DF.DynamicLink | None
		target_doctype: DF.Link | None
		task: DF.Link
	# end: auto-generated types

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
		doc = cast(OttoSession, frappe.get_doc({"doctype": "Otto Session", "task": task}))

		doc.target_doctype = target_doctype
		doc.target = target
		doc.event = event

		doc.llm = llm or frappe.get_cached_value("Otto Task", task, "llm")
		doc.instruction = instruction or frappe.get_cached_value("Otto Task", task, "instruction")
		if reasoning_effort and reasoning_effort in ["None", "Low", "Medium", "High"]:
			doc.reasoning_effort = reasoning_effort  # type: ignore
		else:
			doc.reasoning_effort = frappe.get_cached_value("Otto Task", task, "reasoning_effort")

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
		from otto.otto.doctype.otto_llm.otto_llm import get_reasoning_effort

		session = json.loads(self.session) if self.session else None
		try:
			interaction, reason = llm.interact(
				context,  # type: ignore needed cause not strong enough type system
				session=session,
				tools=get_tools(self.task),
				model=self.llm,
				system=self.instruction,
				reasoning_effort=get_reasoning_effort(self.reasoning_effort),
			)
			logger.info(
				{
					"message": "interact success",
					"session": self.name,
					"session_size": interaction and len(interaction["update"]),
					"item": interaction and interaction["item"],
				}
			)
		except Exception as e:
			otto.log_error(title="interact error", doc=self)
			self.set_status("Failure", f"Interaction errored out: {e}")
			return

		if interaction is None:
			self.set_status("Failure", reason)
			return

		self.set_session(interaction["update"])

		item = interaction["item"]
		if self.run_tools(item, interaction["update"]):
			return self.set_status("Success")

		if self.should_stop(item):
			return self.set_status("Success")

		self.loop(None)

	def should_stop(self, item: SessionItem) -> bool:
		"""
		This has been added cause Gemini 2.5 Flash did not call end_task and
		instead so for smaller models, this check should suffice until a better
		solution is found.
		"""
		if item["meta"]["end_reason"] != "turn_end":
			return False

		return item["meta"]["output_tokens"] == 0

	def run_tools(self, item: SessionItem, session: Session):
		"""Runs tools and checks if meta tool end_task is used"""
		from otto.otto.doctype.otto_task.otto_task import OttoTask

		task = otto.get(OttoTask, self.task)
		env_map = {t.name: t.env for t in task.tools}
		tool_map = get_tool_map(task)

		# Move meta tools to the end of the list
		content = sorted(item["content"], key=lambda x: is_meta_tool(x))

		task_ended = False
		for content in item["content"]:
			if content["type"] != "tool_use":
				continue

			result = None
			is_error = False
			if is_meta_tool(content):
				task_ended = task_ended or has_task_ended(content)
			else:
				tool_name = tool_map[content["name"]]
				env_str = env_map.get(tool_name, None)
				result, is_error = self.execute_tool(tool_name, content["args"], env_str)

			llm.update_with_tool_result(session=session, result=result, id=content["id"], is_error=is_error)
			self.set_session(session)
		return task_ended

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

	def set_session(self, session: Session):
		self.session = json.dumps(session, indent=2)
		self.save(ignore_permissions=True, ignore_version=True)
		frappe.db.commit()

	def set_status(
		self,
		status: Literal["Pending", "Running", "Success", "Failure"],
		reason: str | None = None,
	):
		self.status = status
		self.reason = reason
		self.save(ignore_permissions=True, ignore_version=True)
		frappe.db.commit()

	def execute_tool(self, tool_name: str, args: dict, env_str: str | None) -> tuple[Any, bool]:
		"""Executes tool and returns tuple of (result, is_error)"""
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		tool_doc = otto.get(OttoTool, tool_name)

		try:
			env = json.loads(env_str) if env_str else None
			return tool_doc.execute(
				args,
				task=self.task,
				session=self.name,
				env=env,
			)["result"], False
		except Exception as e:
			otto.log_error(
				"Tool Use Error",
				doc=self,
				tool=tool_name,
			)
			return str(e), True

	@frappe.whitelist()
	def get_stats(self):
		if not self.session:
			return "No Session"

		session: Session = json.loads(self.session)
		return llm.get_stats(session)

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


def get_tool_map(task: OttoTask) -> dict[str, str]:
	"""returns dict[slug, name]"""
	names = [t.tool for t in task.tools if not t.slug and t.is_enabled]
	_tool_map = {
		t.name: t.slug
		for t in frappe.get_all("Otto Tool", filters={"name": ("in", names)}, fields=["slug", "name"])
	}

	tool_map = {}
	for t in task.tools:
		if not t.is_enabled:
			continue

		slug = t.slug or _tool_map[t.tool]
		tool_map[slug] = t.tool
	return tool_map


@frappe.whitelist()
def get_recent_sessions(limit: int = 20) -> list[dict]:
	sessions = frappe.get_all(
		"Otto Session",
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
def get_adjacent_session(name: str, next: str | bool):
	if isinstance(next, str):
		"""frappe.call appears to be sending a string instead of a boolean, wt"""
		next = next == "true"

	"""Get the next or previous session in chronological order"""
	order = "asc" if next else "desc"
	operator = ">" if next else "<"

	session = frappe.get_all(
		"Otto Session",
		filters={
			"modified": (operator, frappe.get_value("Otto Session", name, "modified")),
		},
		order_by=f"modified {order}",
		limit=1,
		pluck="name",
	)

	if session:
		return session[0]

	return None
