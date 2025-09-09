# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

from typing import Any

import frappe
from frappe import _

from otto.otto.report.utils import get_group_by_and_period, set_periodicity


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	filters = filters or {}
	set_periodicity(filters)

	data = get_data(filters or {})
	columns = get_columns(filters)
	return columns, data


def get_columns(filters: dict) -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""

	return [
		{
			"label": _("Period"),
			"fieldname": "period",
			"fieldtype": "Data",
			"width": 100,
		},
		# Totals
		{
			"label": _("Total Sessions"),
			"description": "Total number of sessions",
			"fieldname": "total_sessions",
			"fieldtype": "Int",
			"width": 90,
		},
		{
			"label": _("Total LLM Calls"),
			"description": "Total number of LLM calls",
			"fieldname": "total_llm_calls",
			"fieldtype": "Int",
			"width": 90,
		},
		{
			"label": _("Total Cost (USD)"),
			"description": "Total cost in USD",
			"fieldname": "total_cost",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("Total Input Tokens"),
			"description": "Total number of tokens input",
			"fieldname": "total_input",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Total Output Tokens"),
			"description": "Total number of tokens output",
			"fieldname": "total_output",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Total Duration (s)"),
			"description": "Total duration per session",
			"fieldname": "total_duration_s",
			"fieldtype": "Float",
			"precision": 3,
			"width": 100,
		},
		# Averages
		{
			"label": _("Avg. LLM Calls"),
			"description": "Average number of LLM calls per session",
			"fieldname": "avg_llm_calls",
			"fieldtype": "Float",
			"precision": 2,
			"width": 90,
		},
		{
			"label": _("Avg. Cost (USD)"),
			"description": "Average cost per session in USD",
			"fieldname": "avg_cost",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("Avg. Input Tokens"),
			"description": "Average number of tokens input per session",
			"fieldname": "avg_input",
			"fieldtype": "Float",
			"precision": 2,
			"width": 130,
		},
		{
			"label": _("Avg. Output Tokens"),
			"description": "Average number of tokens output per session",
			"fieldname": "avg_output",
			"fieldtype": "Float",
			"precision": 2,
			"width": 130,
		},
		{
			"label": _("Avg. Duration (s)"),
			"description": "Average duration per session",
			"fieldname": "avg_duration_s",
			"fieldtype": "Float",
			"width": 100,
			"precision": 3,
		},
		{
			"label": _("Avg. Rate (TPS)"),
			"description": "Average tokens per second",
			"fieldname": "avg_rate_tps",
			"fieldtype": "Float",
			"width": 100,
			"precision": 3,
		},
		{
			"label": _("Avg. TTFC (s)"),
			"description": "Average time to first chunk",
			"fieldname": "avg_ttfc_s",
			"fieldtype": "Float",
			"width": 100,
			"precision": 3,
		},
		{
			"label": _("Avg. Latency (ms)"),
			"description": "Average inter-chunk latency",
			"fieldname": "avg_latency_ms",
			"fieldtype": "Float",
			"width": 100,
			"precision": 3,
		},
	]


def get_data(filters: dict) -> list[list[Any]]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	cte_conditions = []
	conditions = []
	values = []
	needs_join = False

	if filters.get("task"):
		conditions.append("ot.name = %s")
		values.append(filters.get("task"))
		needs_join = True

	if filters.get("from_date"):
		conditions.append("os.creation >= %s")
		values.append(filters.get("from_date"))

	if filters.get("to_date"):
		conditions.append("os.creation <= %s")
		values.append(filters.get("to_date"))

	if filters.get("llm"):
		cte_conditions.append("os.llm = %s")
		values.append(filters.get("llm"))

	if filters.get("event"):
		conditions.append("ex.event = %s")
		values.append(filters.get("event"))
		needs_join = True

	joins = ""
	if needs_join:
		joins = (
			"join `tabOtto Execution` as ex on ex.session = os.name "
			"left join `tabOtto Task` as ot on ex.task = ot.name"
		)

	where_clause = ""
	if conditions:
		where_clause = "AND " + " AND ".join(conditions)

	cte_where_clause = ""
	if cte_conditions:
		cte_where_clause = "AND " + " AND ".join(cte_conditions)

	group_by, period = get_group_by_and_period(filters, "os")
	query = f"""
	with os as (
		select
			os.name as name,
			count(*) as llm_calls,
			min(osi.creation) as creation,
			sum(osi.cost) as total_cost,
			sum(osi.input_tokens) as total_input,
			sum(osi.output_tokens) as total_output,
			timestampdiff(second, min(osi.timestamp), max(osi.end_time)) as duration_s,

			sum(osi.output_tokens / timestampdiff(second, osi.start_time, osi.end_time)) as total_rate_tps,
			sum(osi.time_to_first_chunk) as total_ttfc_s,
			sum(osi.inter_chunk_latency) * 1000 as total_latency_ms
		from
			`tabOtto Session` as os
			join `tabOtto Session Item CT` as osi on osi.parent = os.name
		where
			osi.role = 'agent'
			{cte_where_clause}
		group by os.name
		order by creation desc
	)
	select
		{period} as period,
		-- Totals
		count(*) as total_sessions,
		sum(os.llm_calls) as total_llm_calls,
		sum(os.total_cost) as total_cost,
		sum(os.total_input) as total_input,
		sum(os.total_output) as total_output,
		sum(os.duration_s) as total_duration_s,

		-- Averages
		avg(os.llm_calls) as avg_llm_calls,
		avg(os.total_cost) as avg_cost,
		avg(os.total_input) as avg_input,
		avg(os.total_output) as avg_output,
		avg(os.duration_s) as avg_duration_s,

		-- Average Timing Stats
		sum(os.total_rate_tps) / GREATEST(sum(os.llm_calls), 0.001) as avg_rate_tps,
		sum(os.total_ttfc_s) / GREATEST(sum(os.llm_calls), 0.001) as avg_ttfc_s,
		sum(os.total_latency_ms) / GREATEST(sum(os.llm_calls), 0.001) as avg_latency_ms
	from
		os
		{joins}
	where
		1=1
		{where_clause}
	group by {group_by}
	order by os.creation desc
	"""

	data: list[list[Any]] = frappe.db.sql(query, values, as_list=True, debug=True) or []  # type: ignore
	return data
