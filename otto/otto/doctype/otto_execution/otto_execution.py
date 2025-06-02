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
	from otto.llm.types import Exchange, ExchangeItem
	from otto.otto.doctype.otto_task.otto_task import OttoTask

logger = otto.logger("otto_execution")


class OttoExecution(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		event: DF.Data | None
		execution: DF.JSON | None
		instruction: DF.Code | None
		llm: DF.Link | None
		reason: DF.SmallText | None
		status: DF.Literal["Pending", "Running", "Success", "Failure"]
		target: DF.DynamicLink
		target_doctype: DF.Link
		task: DF.Link
	# end: auto-generated types

	@staticmethod
	def new(
		task: str,
		*,
		target: str,
		target_doctype: str,
		event: str | None = None,
		llm: str | None = None,
		instruction: str | None = None,
	):
		doc = cast(OttoExecution, frappe.get_doc({"doctype": "Otto Execution", "task": task}))

		if target and event:
			doc.target_doctype = target_doctype
			doc.target = target
			doc.event = event

		doc.llm = llm or frappe.get_cached_value("Otto Task", task, "llm")
		doc.instruction = instruction or frappe.get_cached_value("Otto Task", task, "instruction")
		doc.save()
		return doc

	def execute(self):
		doc = frappe.get_doc(self.target_doctype, self.target)
		self.set_status("Running")
		if not (context := self.get_context(doc, self.event or "Manual")):
			return

		self.loop(context)

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
		exchange = json.loads(self.execution) if self.execution else None
		try:
			interaction, reason = llm.interact(
				context,  # type: ignore needed cause not strong enough type system
				exchange=exchange,
				tools=get_tools(self.task),
				model=self.llm,
				system=self.instruction,
			)
			logger.info(
				{
					"message": "interact success",
					"execution": self.name,
					"exchange_size": interaction and len(interaction["update"]),
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

		self.set_execution(interaction["update"])

		item = interaction["item"]
		if self.run_tools(item, interaction["update"]):
			return self.set_status("Success")

		self.loop(None)

	def run_tools(self, item: ExchangeItem, exchange: Exchange):
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

			llm.update_with_tool_result(exchange=exchange, result=result, id=content["id"], is_error=is_error)
			self.set_execution(exchange)
		return task_ended

	def get_context(self, doc: Document, event: str):
		from otto.otto.doctype.otto_task.otto_task import run_get_context

		get_context = frappe.get_value("Otto Task", self.task, "get_context")
		if not get_context or not isinstance(get_context, str):
			return doc.as_json()

		try:
			context = run_get_context(get_context, doc, event)
		except Exception as e:
			otto.log_error(title="get_context error", doc=self)
			self.set_status("Failure", str(e))
			return None

		return context

	def set_execution(self, execution: Exchange):
		self.execution = json.dumps(execution, indent=2)
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
				execution=self.name,
				env=env,
			)["result"], False
		except Exception as e:
			logger.error(
				{
					"execution": self.name,
					"message": "tool use error",
					"tool": tool_name,
					"error": e,
				}
			)
			return str(e), True

	@frappe.whitelist()
	def get_stats(self):
		if not self.execution:
			return "No Execution"

		exchange: Exchange = json.loads(self.execution)
		return llm.get_stats(exchange)


def get_tool_map(task: OttoTask) -> dict[str, str]:
	"""returns dict[slug, name]"""
	names = [t.name for t in task.tools]
	tool_map = {
		t.slug: t.name
		for t in frappe.get_all("Otto Tool", filters={"name": ("in", names)}, fields=["slug", "name"])
	}

	# Update tool map with overridden slugs
	# such is in the case of duplicate tools
	dupes = {t.slug: t.name for t in task.tools if t.slug}
	tool_map.update(dupes)

	return tool_map
