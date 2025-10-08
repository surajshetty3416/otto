from typing import TYPE_CHECKING, Any

import frappe

import otto
from otto.llm.utils import get_sequence
from otto.otto.doctype.otto_task.tools import is_meta_tool

if TYPE_CHECKING:
	from otto.llm.types import SessionItem


@frappe.whitelist()
def get_session_view(name: str):
	"""
	Returns data required by the session viewer, including linked execution (if
	exists), tools, task and LLM info.
	"""
	from otto.otto.doctype.otto_llm.otto_llm import OttoLLM
	from otto.otto.doctype.otto_session.otto_session import OttoSession

	doc = otto.get(OttoSession, name)
	session = doc._get_session()

	info: dict[str, Any] = dict(
		name=doc.name,
		session=doc.as_dict(convert_dates_to_str=True),
		stats=doc.get_stats(),
	)

	if session is not None:
		info["sequence"] = get_sequence(session)

	if doc.llm:
		llm = otto.get(OttoLLM, doc.llm)
		info["llm"] = llm.as_dict(convert_dates_to_str=True)

	set_execution_info(name, info)
	set_tools_info(name, info)
	set_scrapbook_info(name, info)
	set_tool_use_info(info)

	return info


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


@frappe.whitelist()
def get_recent_sessions(limit: int = 20, page: int = 0) -> list[dict]:
	sessions = frappe.get_all(
		"Otto Session",
		fields=["name", "creation"],
		limit=limit,
		order_by="modified desc",
		limit_start=page * limit,
	)

	executions = frappe.get_all(
		"Otto Execution",
		filters={"session": ("in", [s["name"] for s in sessions])},
		fields=["name", "status", "task", "target", "target_doctype", "session"],
		limit=limit,
		order_by="modified desc",
	)

	tasks = frappe.get_all(
		"Otto Task", filters={"name": ("in", [e["task"] for e in executions])}, fields=["name", "title"]
	)

	task_map = {t["name"]: t for t in tasks}
	execution_map = {e["session"]: e for e in executions}

	for s in sessions:
		if s["name"] not in execution_map:
			s["execution"] = "-"
			s["status"] = "-"
			s["task"] = "-"
			s["target"] = "-"
			s["target_doctype"] = "-"
			s["task_name"] = "-"
			continue

		e = execution_map[s["name"]]
		s["execution"] = e["name"]
		s["status"] = e["status"]
		s["task"] = e["task"]
		s["target"] = e["target"]
		s["target_doctype"] = e["target_doctype"]
		s["task_name"] = task_map[e["task"]]["title"]

	return sessions


def set_execution_info(session_name: str, info: dict[str, Any]):
	from otto.otto.doctype.otto_execution.otto_execution import OttoExecution

	execs = frappe.get_list(
		"Otto Execution",
		filters={"session": session_name},
		pluck="name",
		limit=1,
	)

	if not execs:
		return

	exec = otto.get(OttoExecution, execs[0])
	info["execution"] = exec.as_dict(convert_dates_to_str=True)
	info["task"] = exec.task
	info["task_title"] = frappe.get_value("Otto Task", exec.task, "title")


def set_tools_info(session_name: str, info: dict[str, Any]):
	"""Return task relevant info for a Task session view."""
	# FIXME: do this for non execution linked sessions
	# session_tools = frappe.get_all(
	# 	"Otto Session Tool CT",
	# 	filters={"parent": session_name},
	# 	fields=["tool", "slug"],
	# )
	# if not session_tools and (task := info.get("task")):
	task = info.get("task")
	if not task:
		return

	session_tools = frappe.get_all(
		"Otto Task Tool CT",
		filters={"parent": task},
		fields=["tool", "slug"],
	)

	tools = frappe.get_all(
		"Otto Tool",
		filters={"name": ["in", [t.tool for t in session_tools]]},
		fields=["name", "slug", "description"],
	)

	slug_map = {}  # slug -> tool.name
	tool_map = {}  # tool.name -> {name,slug,description,slug_actual}

	for t in tools:
		t.slug_actual = t.slug
		tool_map[t.name] = t

	for st in session_tools:
		if st.slug:  # override
			slug_map[st.slug] = st.tool
			tool_map[st.tool]["slug"] = st.slug
		else:
			slug = tool_map[st.tool]["slug"]
			slug_map[slug] = st.tool

	info["tool_map"] = tool_map
	info["slug_map"] = slug_map

	# Set tool info on session items for convenience
	for si in info.get("sequence", []):
		for c in si.get("content", []):
			if c["type"] != "tool_use":
				continue
			tool_name = slug_map.get(c["name"])
			c["tool"] = tool_map.get(tool_name)


def set_tool_use_info(info: dict[str, Any]):
	sequence: list[SessionItem] = info.get("sequence", [])
	if not sequence:
		return

	tool_use = {}

	slug_map = info.get("slug_map")
	tool_map = info.get("tool_map")

	if not slug_map or not tool_map:
		return

	for i, item in enumerate(sequence):
		for j, c in enumerate(item.get("content", [])):
			if c["type"] != "tool_use":
				continue

			slug = c["name"]
			result = c.get("result", None)
			status = c.get("status", "pending")
			name = slug_map.get(slug)
			tool = tool_map.get(name, {})

			if slug not in tool_use:
				tool_use[slug] = {
					"call_count": 0,
					"empty_result_count": 0,
					"error_count": 0,
					"name": name,
					"slug": slug,
					"slug_original": tool.get("slug", slug),
					"description": tool.get("description", ""),
					"calls": [],
					"is_meta": is_meta_tool(c),
					"total_duration": 0,
				}

			tool_use[slug]["call_count"] += 1
			tool_use[slug]["total_duration"] += c.get("end_time", 0) - c.get("start_time", 0)

			if result is None or result == "" or result == "null" or result == "[]" or result == "{}":
				tool_use[slug]["empty_result_count"] += 1

			if status == "error" or (isinstance(result, str) and ("Error" in result or "error" in result)):
				tool_use[slug]["error_count"] += 1

			call = {
				"index": (i, j),  # session item index, content index
				"result": result,
				"args": c.get("args", {}),
				"override": c.get("override", {}),
				"status": status,
				"start_time": c.get("start_time", 0),
				"end_time": c.get("end_time", 0),
				"stdout": c.get("stdout", None),
				"stderr": c.get("stderr", None),
			}
			tool_use[slug]["calls"].append(call)

	info["tool_use"] = tool_use


def set_scrapbook_info(session_name: str, info: dict[str, Any]):
	scrapbooks = frappe.get_all(
		"Otto Scrapbook",
		filters={"session": session_name},
		fields=["name", "content", "tool", "creation"],
	)

	info["scrapbooks"] = scrapbooks

	if not (tool_map := info.get("tool_map")):
		return

	for sb in scrapbooks:
		sb["tool_slug"] = tool_map.get(sb.tool, {}).get("slug")
