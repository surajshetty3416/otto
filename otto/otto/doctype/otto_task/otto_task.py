# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
from typing import Any, cast

import frappe
from frappe.model.document import Document
from frappe.utils.safe_exec import get_safe_globals

import otto
from otto.otto.doctype.otto_task.tools import meta_tools

logger = otto.logger("otto_task")

EVENT_MAP = {
	"after_insert": "On Create",
	"on_update": "On Update",
	"on_delete": "On Delete",
	"on_submit": "On Submit",
	"on_cancel": "On Cancel",
	"manual": "Manual",
}


class OttoTask(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_task_tool_ct.otto_task_tool_ct import OttoTaskToolCT

		condition: DF.Code | None
		event: DF.Literal["On Create", "On Update", "On Delete", "On Submit", "On Cancel", "Manual"]
		get_context: DF.Code | None
		instruction: DF.Code | None
		is_enabled: DF.Check
		llm: DF.Link | None
		target_doctype: DF.Link
		title: DF.Data | None
		tools: DF.Table[OttoTaskToolCT]
	# end: auto-generated types

	@staticmethod
	def new(
		title: str,
		event: str,
		target_doctype: str,
		*,
		llm: str | None = None,
		condition: str | None = None,
		get_context: str | None = None,
		instruction: str | None = None,
		tools: list[dict] | None = None,
	):
		doc = cast(
			OttoTask,
			frappe.get_doc(
				{
					"doctype": "Otto Task",
					"title": title,
					"target_doctype": target_doctype,
					"event": event,
				}
			),
		)

		doc.llm = llm
		doc.condition = condition
		doc.get_context = get_context
		doc.instruction = instruction

		for tool in tools or []:
			doc.append("tools", {"tool": tool["tool"]})

		doc.save()
		return doc

	@frappe.whitelist()
	def execute_task(self, target: str, llm: str):
		return self.trigger_execution(
			target=target,
			event="Manual",
			llm=llm,
			is_background=True,
		)

	def trigger_execution(
		self,
		*,
		target: str,
		event: str,
		llm: str | None = None,
		instruction: str | None = None,
		is_background: bool = True,
	):
		from otto.otto.doctype.otto_execution.otto_execution import OttoExecution

		assert self.name is not None, "type check"
		execution = OttoExecution.new(
			self.name,
			target=target,
			target_doctype=self.target_doctype,
			event=event,
			llm=llm,
			instruction=instruction,
		)
		frappe.db.commit()
		logger.info(
			{
				"message": "starting execution",
				"execution": execution.name,
				"task": self.name,
				"doc": f"{self.target_doctype}, {target}",
				"event": event,
			}
		)

		if is_background:
			frappe.enqueue_doc(
				doctype="Otto Execution",
				name=execution.name,
				method="execute",
				timeout=get_timeout(),
			)
			return execution.name

		return execution.execute()

	@frappe.whitelist()
	def test_get_context(self, target: str):
		from otto.utils.execute import run_get_context

		assert self.get_context is not None, "type check"
		return run_get_context(
			self.get_context,
			doc=frappe.get_doc(self.target_doctype, target),
			event="Manual",
		)

	@frappe.whitelist()
	def list_tools(self):
		assert self.name is not None, "type check"
		return get_tools(self.name)

	@frappe.whitelist()
	def export_task(self):
		llm = frappe.get_all("Otto LLM", filters={"name": self.llm}, fields=["name", "title", "provider"])[0]
		data: dict = dict(
			title=self.title,
			llm=llm,
			event=self.event,
			condition=self.condition,
			get_context=self.get_context,
			instruction=self.instruction,
			target_doctype=self.target_doctype,
			tools=[],
			groups=[],
		)

		tool_names = [tool.tool for tool in self.tools if tool.is_enabled]
		tools = frappe.get_all(
			"Otto Tool",
			filters={"name": ("in", tool_names)},
			fields=[
				"name",
				"slug",
				"description",
				"code",
				"group",
				"is_valid",
				"mock_tool",
				"mock_return_value",
			],
		)
		tool_map = {tool.name: tool for tool in tools}

		args = frappe.get_all(
			"Otto Tool Arg CT",
			filters={"parent": ("in", tool_names)},
			fields=["parent", "arg_name", "type", "is_required", "description"],
		)
		for arg in args:
			tool_map.get(arg.parent, {}).setdefault("args", []).append(
				{
					"arg_name": arg.arg_name,
					"type": arg.type,
					"is_required": arg.is_required,
					"description": arg.description,
				}
			)

		slug_map = {t.name: t.slug for t in tools}
		for tool in tools:
			if not tool.get("is_valid"):
				raise frappe.ValidationError(f"Tool {tool.get('slug')} is not valid")

			del tool["name"]
			del tool["is_valid"]
			data["tools"].append(tool)

		groups = list(set([tool.group for tool in tools if tool.group]))
		data["groups"] = frappe.get_all(
			"Otto Tool Group",
			filters={"name": ("in", groups)},
			fields=["name", "description"],
		)

		# (actual slug, override slug)
		data["task_tools"] = [(slug_map.get(t.tool), t.slug or None) for t in self.tools if t.is_enabled]

		return data


def common_handler(doctype: Document, event: str | None = None):
	"""
	Common handler function is used to enqueue tasks for a given doctype and
	event. When an Otto Task is created or updated, the otto.hooks.doc_events is
	updated with for the given doctype and event is updated with this function.
	"""
	if not otto.is_enabled() or not event or event not in EVENT_MAP:
		return

	event_label = EVENT_MAP[event]

	# TODO: Cache this get_all call, update only every 5 minutes or something
	for task in frappe.db.get_all(
		"Otto Task",
		filters={"target_doctype": doctype.doctype, "event": event_label},
		fields=["name", "condition"],
	):
		if task.condition and not test_condition(
			task.name,
			task.condition,
			doctype,
		):
			continue

		logger.info(
			{
				"message": "handler enqueued",
				"otto_task": task.name,
				"doctype": doctype.doctype,
				"name": doctype.name,
				"event": event,
			}
		)
		frappe.enqueue(
			handler,
			timeout=get_timeout(),
			# Args
			task=task.name,
			target_doc=doctype,
			target_event=event_label,
		)


def handler(task: str, target_doc: Document, target_event: str):
	"""Handler function is used to handle the Otto Task."""
	assert target_doc.name is not None, "typecheck"

	return otto.get(OttoTask, task).trigger_execution(
		target=target_doc.name,
		event=target_event,
		is_background=False,
	)


def get_tools(task: str):
	from otto.otto.doctype.otto_tool.otto_tool import OttoTool

	tools = []
	for tool in frappe.get_all(
		"Otto Task Tool CT",
		fields=["tool", "slug"],
		filters={"parent": task, "is_enabled": True},
	):
		tool_doc = otto.get(OttoTool, tool.tool)
		if not tool_doc.is_valid:
			continue

		tools.append(tool_doc.get_function_schema(tool.slug))

	tools.extend(meta_tools)
	return tools


def get_timeout():
	return frappe.get_cached_value("Otto Settings", "Otto Settings", "task_execution_timeout") * 60


def test_condition(task: str, condition: str, doc: Document) -> bool:
	from frappe.integrations.doctype.webhook.webhook import get_context

	try:
		results = frappe.safe_eval(
			condition,
			eval_locals=get_context(doc),
		)

		return bool(results)

	except Exception:
		otto.log_error(
			"Error evaluating condition",
			task=task,
			condition=condition,
			target_name=doc.name,
			target_doctype=doc.doctype,
		)

	return False


@frappe.whitelist()
def import_task(data: str):
	_data = json.loads(data)

	from otto.otto.doctype.otto_tool.otto_tool import OttoTool
	from otto.otto.doctype.otto_tool_group.otto_tool_group import OttoToolGroup

	llm = _data["llm"]
	if not frappe.db.exists("Otto LLM", llm["name"]):
		from otto.otto.doctype.otto_llm.otto_llm import OttoLLM

		OttoLLM.new(llm["name"], llm["title"], llm["provider"])

	for group in _data["groups"]:
		if not frappe.db.exists("Otto Tool Group", group["name"]):
			OttoToolGroup.new(group["name"], group["description"])

	slug_map = {}  # dict[tool_name, tool_slug]
	for t in _data["tools"]:
		tool = OttoTool.new(
			t["slug"],
			t["description"],
			t["code"],
			group=t.get("group", None),
			args=t.get("args", []),
			mock_tool=t.get("mock_tool", False),
			mock_return_value=t.get("mock_return_value", None),
		)
		slug_map[tool.slug] = tool.name

	task = OttoTask.new(
		_data["title"],
		_data["event"],
		_data["target_doctype"],
		llm=_data["llm"]["name"],
		condition=_data["condition"],
		get_context=_data["get_context"],
		instruction=_data["instruction"],
		tools=[{"tool": slug_map[a], "slug": o} for a, o in _data["task_tools"]],
	)

	return task.name
