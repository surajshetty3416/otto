# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

from typing import Any

import frappe
from frappe import _


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	data = get_data(filters or {})

	return columns, data


def get_columns() -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
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
			"hidden": 1,
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
			"width": 300,
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


def get_data(filters: dict) -> list[list[Any]]:
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
	SELECT
		ex.name as execution,
		ex.task as task,
		ex.target,
		ex.target_doctype,
		ex.event,
		os.llm,
		SUM(osi.cost) as total_cost,
		COUNT(*) as llm_calls,
		SUM(osi.input_tokens) as total_input,
		SUM(osi.output_tokens) as total_output,
		MAX(osi.input_tokens) as max_input,
		MAX(osi.output_tokens) as max_output,
		TIMESTAMPDIFF(SECOND, MIN(osi.timestamp), MAX(osi.end_time)) as duration_s,
		AVG(osi.output_tokens / TIMESTAMPDIFF(SECOND, osi.start_time, osi.end_time)) as rate_tps,
		AVG(osi.time_to_first_chunk) as ttfc_s,
		AVG(osi.inter_chunk_latency) * 1000 as latency_ms
	FROM
		`tabOtto Session` as os
		JOIN `tabOtto Session Item CT` osi ON os.name = osi.parent
		JOIN `tabOtto Execution` as ex ON ex.session = os.name
		LEFT JOIN `tabOtto Task` as ot ON ex.task = ot.name
	WHERE
		osi.role = 'agent'
		{where_clause}
	GROUP BY osi.parent
	ORDER BY os.creation DESC
	"""

	return frappe.db.sql(query, values, as_list=True) or []  # type: ignore
