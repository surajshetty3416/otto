# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, cast

import frappe
from frappe.model.document import Document

import otto
from otto import utils
from otto.lib.utils import is_reasoning_effort
from otto.otto.doctype.otto_task.tools import is_meta_tool, meta_tools

if TYPE_CHECKING:
	from otto.llm.types import ReasoningEffort

logger = otto.logger("otto.doctype.otto_task", "DEBUG")

DEFAULT_TIMEOUT = 30
EVENT_MAP = {
	"after_insert": "On Create",
	"on_update": "On Update",
	"on_delete": "On Delete",
	"on_submit": "On Submit",
	"on_cancel": "On Cancel",
	"manual": "Manual",
}


class ToolMapItem(NamedTuple):
	tool_name: str | None
	env_str: str | None
	requires_permission: bool


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
		no_target: DF.Check
		reasoning_effort: DF.Literal["None", "Low", "Medium", "High"]
		target_doctype: DF.Link | None
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
		reasoning_effort: str | None = None,
	):
		doc = cast(
			"OttoTask",
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

		if reasoning_effort and reasoning_effort in ["None", "Low", "Medium", "High"]:
			doc.reasoning_effort = reasoning_effort  # type: ignore

		for tool in tools or []:
			doc.append("tools", tool)

		doc.save()
		return doc

	@frappe.whitelist()
	def execute_task(self, target: str, llm: str | None, reasoning_effort: str | None = None):
		if not is_reasoning_effort(reasoning_effort):
			reasoning_effort = None

		return self.trigger_execution(
			target=target,
			event="Manual",
			llm=llm,
			reasoning_effort=reasoning_effort,
			is_background=True,
		)

	def before_save(self):
		self.set_if_no_target()
		self.set_reasoning()

	def validate(self):
		if self.no_target and not self.get_context:
			raise frappe.ValidationError("get_context cannot be empty if No Target is set")

		for tool in self.tools:
			if tool.slug and is_meta_tool(tool.slug):
				raise frappe.ValidationError(f'Slug cannot be named "{tool.slug}" as it is a meta tool')

	def set_if_no_target(self):
		if self.target_doctype and not self.no_target:
			return

		assert self.no_target, "sanity check"
		self.target_doctype = None
		self.event = "Manual"

	def set_reasoning(self):
		if not self.llm or self.reasoning_effort == "None":
			self.reasoning_effort = "None"
			return

		if not frappe.get_cached_value("Otto LLM", self.llm, "is_reasoning"):
			self.reasoning_effort = "None"

	def trigger_execution(
		self,
		*,
		target: str | None,
		event: str,
		llm: str | None = None,
		reasoning_effort: ReasoningEffort | None = None,
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
			reasoning_effort=reasoning_effort,
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
	def test_get_context(self, target: str, as_content: bool = False):
		assert self.get_context is not None, "type check"
		doc = None
		if not self.no_target:
			assert self.target_doctype is not None, "type check, sanity check"
			doc = frappe.get_doc(self.target_doctype, target)

		context = run_get_context(
			get_context=self.get_context,
			doc=doc,
			event="Manual",
		)

		if as_content:
			from otto.llm.utils import to_content

			return to_content(context)

		return context

	@frappe.whitelist()
	def list_tools(self):
		assert self.name is not None, "type check"
		return get_tools(self.name)


def common_handler(doctype: Document, event: str | None = None):
	try:
		return _common_handler(doctype, event)
	except Exception:
		otto.log_error(title="common_handler error", doc=doctype, event=event)


def _common_handler(doctype: Document, event: str | None = None):
	"""
	Common handler function is used to enqueue tasks for a given doctype and
	event. When an Otto Task is created or updated, the otto.hooks.doc_events is
	updated with for the given doctype and event is updated with this function.
	"""
	if not otto.is_enabled() or not event or event not in EVENT_MAP:
		return

	event_label = EVENT_MAP[event]

	for task in _get_all_tasks(doctype.doctype, event_label):
		if task.condition and not test_condition(
			task.name,
			task.condition,
			doctype,
		):
			logger.debug(
				{
					"message": "test_condition false",
					"task": task.name,
					"name": doctype.name,
					"doctype": doctype.doctype,
					"event": event,
				}
			)
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
			enqueue_after_commit=True,
			# Args
			task=task.name,
			target_doc=doctype,
			target_event=event_label,
		)


@utils.cache(ttl=60)
def _get_all_tasks(target_doctype: str, event: str):
	return frappe.get_all(
		"Otto Task",
		filters={"target_doctype": target_doctype, "event": event, "is_enabled": True},
		fields=["name", "condition"],
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


def get_tool_map(task: str) -> dict[str, ToolMapItem]:
	"""
	returns dict[slug, (tool_name, env_str, requires_permission)]

	returned map does not contain meta tools

	slug: slug name given to the session (i.e. overriden name or actual if present)
	tool_name: name of the Otto Tool doc
	env_str: env string on the Task Tool CT item used during execution
	requires_permission: whether the tool requires permission
	"""
	task_tools = frappe.get_all(
		"Otto Task Tool CT",
		filters={"parent": task},
		fields=["tool", "slug", "env"],
	)
	tool_slugs = frappe.get_all(
		"Otto Tool",
		filters={"name": ("in", [t.tool for t in task_tools])},
		fields=["name", "slug", "requires_permission"],
	)
	tool_slug_map = {t.name: t.slug for t in tool_slugs}
	permission_map = {t.name: t.requires_permission for t in tool_slugs}

	tool_map = {}
	for tool in task_tools:
		# slug = override slug or primary slug
		slug = tool.get("slug") or tool_slug_map.get(tool.tool)
		if not slug:
			continue

		tool_map[slug] = ToolMapItem(
			tool_name=tool.get("tool"),
			env_str=tool.get("env"),
			requires_permission=permission_map.get(tool.tool, False),
		)
	return tool_map


def get_timeout() -> int:
	timeout = frappe.get_cached_value("Otto Settings", "Otto Settings", "task_execution_timeout")
	if timeout is None:
		return DEFAULT_TIMEOUT * 60

	if not isinstance(timeout, int):
		timeout = int(timeout)

	return timeout * 60


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


def run_get_context(get_context: str, doc: Document | None, event: str):
	if not get_context and doc:
		return doc.as_json()

	from otto.otto.doctype.otto_tool.lib import get_lib
	from otto.utils import execute, json_dumps

	context = execute.execute(
		script=get_context,
		args=dict(doc=doc, event=event),
		arg_names=["doc", "event"],
		globals=dict(otto=get_lib()),
		function_name="get_context",
	)

	result = context["result"]

	if isinstance(result, str):
		return result

	if not isinstance(result, list):
		return json_dumps(result)[0]

	from otto.llm.utils import is_user_content

	content = []
	for r in result:
		if is_user_content(r) or isinstance(r, str):
			content.append(r)
		else:
			content.append(json_dumps(r)[0])

	return content


@utils.cache(ttl=60)
def get_tool_name(task: str, slug: str) -> str | None:
	tool = frappe.get_all(
		"Otto Task Tool CT",
		filters={"parent": task, "slug": slug},
		fields=["tool"],
		pluck="tool",
		limit=1,
	)
	if tool:
		return tool[0]

	tool = frappe.get_all(
		"Otto Tool",
		filters={"slug": slug},
		fields=["name"],
		pluck="name",
		limit=1,
	)
	if tool:
		return tool[0]

	return None
