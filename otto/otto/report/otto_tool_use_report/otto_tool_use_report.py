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
		{
			"label": _("Tool"),
			"fieldname": "tool",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Times Called"),
			"fieldname": "times_called",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Avg Duration"),
			"fieldname": "avg_duration",
			"fieldtype": "Float",
			"width": 120,
			"precision": 3,
		},
		{
			"label": _("Total Duration"),
			"fieldname": "total_duration",
			"fieldtype": "Float",
			"width": 120,
			"precision": 3,
		},
		{
			"label": _("Success Count"),
			"fieldname": "num_success",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Pending Count"),
			"fieldname": "num_pending",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Error Count"),
			"fieldname": "num_error",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Empty Count"),
			"fieldname": "num_empty",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Success %"),
			"fieldname": "percent_success",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Pending %"),
			"fieldname": "percent_pending",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Error %"),
			"fieldname": "percent_error",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Empty %"),
			"fieldname": "percent_empty",
			"fieldtype": "Percent",
			"width": 100,
		},
	]


def get_data(filters: dict) -> list[list[Any]]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	conditions = []
	values = []

	if filters.get("from_date"):
		conditions.append("osi.creation >= %s")
		values.append(filters.get("from_date"))

	if filters.get("to_date"):
		conditions.append("osi.creation <= %s")
		values.append(filters.get("to_date"))

	where_clause = ""
	if conditions:
		where_clause = "AND " + " AND ".join(conditions)

	group_by, period = get_group_by_and_period(filters, "jt")
	query = f"""
		with jt as (
			select
				osi.creation as creation,
				jt.tool as tool,
				ifnull(jt.end - jt.start, 0) as duration,
				if(jt.status = "success", 1, 0) as is_success,
				if(jt.status = "error", 1, 0) as is_error,
				if(jt.status = "pending", 1, 0) as is_pending,
				if(
					jt.result = "[]" or
					jt.result = "{{}}" or
					jt.result = "" or
					jt.result = "null" or
					isnull(jt.result), 1, 0
				) as is_empty
			from `tabOtto Session Item CT` osi,
			json_table(
				osi.content, '$[*]' columns(
				type text path '$.type',
				tool text path '$.name',
				start float path '$.start_time',
				end float path '$.end_time',
				status text path '$.status',
				result text path '$.result'
				)
			) as jt
			where jt.type = 'tool_use' {where_clause}
		)
		select
		{period} as period,
		jt.tool as tool,
		count(*) as times_called,
		avg(duration) as avg_duration,
		sum(duration) as total_duration,
		-- counts
		sum(is_success) as num_success,
		sum(is_pending) as num_pending,
		sum(is_error) as num_error,
		sum(is_empty) as num_empty,
		-- percents
		100 * sum(is_success) / count(*) as percent_success,
		100 * sum(is_pending) / count(*) as percent_pending,
		100 * sum(is_error) / count(*) as percent_error,
		100 * sum(is_empty) / count(*) as percent_empty
		from jt
		group by {group_by}, tool
		order by {group_by} desc, tool
	"""

	data: list[list[Any]] = frappe.db.sql(query, values, as_list=True, debug=True) or []  # type: ignore
	return data
