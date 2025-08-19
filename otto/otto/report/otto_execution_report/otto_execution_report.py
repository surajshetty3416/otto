# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

from typing import Any

import frappe
import frappe.utils
from frappe import _


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	filters = filters or {}
	if not filters.get("from_date") and not filters.get("to_date"):
		now = frappe.utils.now_datetime()
		filters["to_date"] = now
		filters["from_date"] = frappe.utils.add_days(now, -7)

	data, session_set = get_data(filters or {})
	columns = get_columns(filters)

	if not filters.get("show_stats"):
		data = [row[:8] for row in data]
		columns = columns[:8]

	#  Show feedback score if enabled
	sessions = list(session_set)
	if filters.get("show_feedback"):
		feedback_cols, feedback_data = get_feedback_cols_and_data(sessions)
		splice_idx = 6
		columns = [*columns[:splice_idx], *feedback_cols, *columns[splice_idx:]]
		data = [[*row[:splice_idx], feedback_data.get(row[0], 0), *row[splice_idx:]] for row in data]

	#  Show tool counts if enabled
	if filters.get("show_tool_counts") and filters.get("task"):
		counts = get_tool_counts(sessions)
		tool_cols, tool_data = get_tool_use_cols_and_data(counts, sessions)

		splice_idx = 7 if filters.get("show_feedback") else 6
		columns = [*columns[:splice_idx], *tool_cols, *columns[splice_idx:]]
		data = [[*row[:splice_idx], *tool_data[row[0]], *row[splice_idx:]] for row in data]

	return columns, data


def get_feedback_cols_and_data(sessions: list[str]) -> tuple[list[dict], dict[str, int]]:
	cols = [
		{
			"label": _("Feedback Score"),
			"fieldname": "feedback_score",
			"fieldtype": "Int",
		}
	]

	query = """
	select
		session,
		sum(value) as score
	from `tabOtto Feedback`
	where session in %s
	group by session
	"""
	res: list[dict] = frappe.db.sql(query, (sessions,), as_dict=True) or []  # type: ignore

	data_map: dict[str, int] = {}
	for r in res:
		data_map[r["session"]] = r["score"] or 0

	return cols, data_map


def get_tool_counts(sessions: list[str]) -> list[dict]:
	"""Return times tool has been called, per tool per session"""
	query = """
	with t as (
		select
			osi.parent as session,
			jt.tool as tool
		from `tabOtto Session Item CT` osi,
		json_table(
			osi.content, '$[*]' columns(
				type text path '$.type',
				tool text path '$.name'
			)
		) as jt
		where jt.type = 'tool_use'
		and osi.parent in %s
	)
	select
		t.session as session,
		t.tool as tool,
		count(*) as times_called
	from t
	group by t.session, t.tool
	"""
	return frappe.db.sql(query, (sessions,), as_dict=True) or []  # type: ignore


def get_tool_use_cols_and_data(
	counts: list[dict], sessions: list[str]
) -> tuple[list[dict], dict[str, list[int]]]:
	"""
	Returns tuple of:
	- columns for tools used and data for each session
	- data of the form dict[session_name, list[tool_use_count]]
	"""
	# dict[session, dict[tool, times_called]]
	st_map: dict[str, dict[str, int]] = {}

	# set of tools called
	tool_set = set()

	for c in counts:
		if c["session"] not in st_map:
			st_map[c["session"]] = {}
		s = st_map[c["session"]]
		if c["tool"] not in s:
			s[c["tool"]] = 0
		s[c["tool"]] += c["times_called"]
		tool_set.add(c["tool"])

	tools: list[str] = list(tool_set)
	tools.sort()

	cols = []
	for tool in tools:
		cols.append(
			{
				"label": tool,
				"description": f"Times '{tool}' was called in a session",
				"fieldname": tool,
				"fieldtype": "Int",
				# "width": 120,
			}
		)

	# ensure all sessions have a row for all tools
	for session in sessions:
		if session in st_map:
			continue

		st_map[session] = {}
		for tool in tools:
			st_map[session][tool] = 0

	data_map: dict[str, list[int]] = {}
	for session, st in st_map.items():
		for t in tools:
			count = st.get(t, 0)
			if session not in data_map:
				data_map[session] = []

			data_map[session].append(count)

	return cols, data_map


def get_columns(filters: dict) -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""

	columns = [
		{
			"label": _("Session"),
			"fieldname": "session",
			"fieldtype": "Link",
			"options": "Otto Session",
			"width": 150,
			"hidden": 1,
		},
		{
			"label": _("Created"),
			"fieldname": "creation",
			"fieldtype": "Datetime",
		},
		{
			"label": _("Execution"),
			"fieldname": "execution",
			"fieldtype": "Link",
			"options": "Otto Execution",
			"width": 150,
		},
		{
			"label": _("Task"),
			"fieldname": "task",
			"fieldtype": "Link",
			"options": "Otto Task",
			"width": 150,
			"hidden": bool(filters.get("task")),
		},
		{
			"label": _("Target"),
			"fieldname": "target",
			"fieldtype": "Dynamic Link",
			"options": "target_doctype",
			"width": 120,
		},
		{
			"label": _("Target DocType"),
			"fieldname": "target_doctype",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 120,
			"hidden": bool(filters.get("task")),
		},
		{
			"label": _("Event"),
			"fieldname": "event",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("LLM"),
			"description": "LLM used for the execution",
			"fieldname": "llm",
			"fieldtype": "Link",
			"options": "Otto LLM",
		},
		{
			"label": _("Cost (USD)"),
			"description": "Total cost of the execution in USD",
			"fieldname": "total_cost",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("LLM Calls"),
			"description": "Total number of LLM calls",
			"fieldname": "llm_calls",
			"fieldtype": "Int",
			"width": 90,
		},
		{
			"label": _("Total Input Tokens"),
			"description": "Total number of tokens input in all calls",
			"fieldname": "total_input",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Total Output Tokens"),
			"description": "Total number of tokens output in all calls",
			"fieldname": "total_output",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Max Input Tokens"),
			"description": "Maximum number of tokens input in a single call",
			"fieldname": "max_input",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Max Output Tokens"),
			"description": "Maximum number of tokens output in a single call",
			"fieldname": "max_output",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Duration (s)"),
			"description": "Total duration of the execution from first to last chunk",
			"fieldname": "duration_s",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Rate (TPS)"),
			"description": "Average tokens per second",
			"fieldname": "rate_tps",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("TTFC (s)"),
			"description": "Average time to first chunk",
			"fieldname": "ttfc_s",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Latency (ms)"),
			"description": "Average inter-chunk latency",
			"fieldname": "latency_ms",
			"fieldtype": "Float",
			"width": 100,
		},
	]

	if filters.get("task") and (
		target_doctype := frappe.get_value("Otto Task", filters.get("task"), "target_doctype")
	):
		columns[3]["label"] = f"{target_doctype} (Target)"

	return columns


def get_data(filters: dict) -> tuple[list[list[Any]], set[str]]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	conditions = []
	values = []

	if filters.get("task"):
		conditions.append("ot.name = %s")
		values.append(filters.get("task"))

	if filters.get("from_date"):
		conditions.append("osi.timestamp >= %s")
		values.append(filters.get("from_date"))

	if filters.get("to_date"):
		conditions.append("osi.timestamp <= %s")
		values.append(filters.get("to_date"))

	if filters.get("llm"):
		conditions.append("os.llm = %s")
		values.append(filters.get("llm"))

	if filters.get("event"):
		conditions.append("ex.event = %s")
		values.append(filters.get("event"))

	where_clause = ""
	if conditions:
		where_clause = "AND " + " AND ".join(conditions)

	query = f"""
	select
		os.name as session,
		os.creation as creation,
		ex.name as execution,
		ex.task as task,
		ex.target,
		ex.target_doctype,
		ex.event,
		os.llm,
		sum(osi.cost) as total_cost,
		count(*) as llm_calls,
		sum(osi.input_tokens) as total_input,
		sum(osi.output_tokens) as total_output,
		max(osi.input_tokens) as max_input,
		max(osi.output_tokens) as max_output,
		timestampdiff(second, min(osi.timestamp), max(osi.end_time)) as duration_s,
		avg(osi.output_tokens / timestampdiff(second, osi.start_time, osi.end_time)) as rate_tps,
		avg(osi.time_to_first_chunk) as ttfc_s,
		avg(osi.inter_chunk_latency) * 1000 as latency_ms
	from
		`tabOtto Session` as os
		join `tabOtto Session Item CT` osi on os.name = osi.parent
		join `tabOtto Execution` as ex on ex.session = os.name
		left join `tabOtto Task` as ot on ex.task = ot.name
	where
		osi.role = 'agent'
		{where_clause}
	group by osi.parent
	order by os.creation desc
	"""

	data: list[list[Any]] = frappe.db.sql(query, values, as_list=True) or []  # type: ignore
	return data, set(i[0] for i in data)
