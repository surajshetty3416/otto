# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt

from typing import Any

import frappe
from frappe import _

from otto.otto.report.utils import get_group_by_and_period, set_periodicity

# TODO: add task and llm filters


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
	return (
		columns,
		data,
		None,
		get_chart_data(data),
		None,
		None,
	)


def get_chart_data(data: list[list[Any]]):
	if not data:
		return None

	positive_values = [float(row[2]) if row[2] is not None else 0 for row in data]
	negative_values = [float(row[3]) if row[3] is not None else 0 for row in data]
	return {
		"data": {
			"labels": [str(row[0]) for row in data],
			"datasets": [
				{"name": "% Positive", "values": positive_values, "chartType": "line"},
				{"name": "% Negative", "values": negative_values, "chartType": "line"},
			],
		},
		"type": "line",
	}


def get_columns(filters: dict) -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
		{
			"label": _("Period"),
			"fieldname": "period",
			"fieldtype": "Data",
		},
		{
			"label": _("Total"),
			"fieldname": "num_total",
			"fieldtype": "Int",
		},
		{
			"label": _("% Positive"),
			"fieldname": "percent_positive",
			"fieldtype": "Percent",
		},
		{
			"label": _("% Negative"),
			"fieldname": "percent_negative",
			"fieldtype": "Percent",
		},
		{
			"label": _("Positive"),
			"fieldname": "num_positive",
			"fieldtype": "Int",
		},
		{
			"label": _("Negative"),
			"fieldname": "num_negative",
			"fieldtype": "Int",
		},
		{
			"label": _("Indifferent"),
			"fieldname": "num_indifferent",
			"fieldtype": "Int",
		},
		{
			"label": _("Has Session"),
			"fieldname": "num_has_session",
			"fieldtype": "Int",
		},
		{
			"label": _("Has Comment"),
			"fieldname": "num_has_comment",
			"fieldtype": "Int",
		},
	]


def get_data(filters: dict) -> list[list[Any]]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	conditions = []
	values = []

	if filters.get("from_date"):
		conditions.append("of.creation >= %s")
		values.append(filters.get("from_date"))

	if filters.get("to_date"):
		conditions.append("of.creation <= %s")
		values.append(filters.get("to_date"))

	where_clause = ""
	if conditions:
		where_clause = "AND " + " AND ".join(conditions)

	# Determine grouping based on periodicity
	group_by, period = get_group_by_and_period(filters, "of")
	query = f"""
		select
			{period} as period,
			count(*) as num_total,
			100.0 * sum(if(of.value = 1, 1, 0)) / count(*) as percent_positive,
			100.0 * sum(if(of.value = -1, 1, 0)) / count(*) as percent_negative,
			sum(if(of.value = 1, 1, 0)) as num_positive,
			sum(if(of.value = -1, 1, 0)) as num_negative,
			sum(if(of.value = 0, 1, 0)) as num_indifferent,
			sum(if(not isnull(of.session), 1, 0)) as num_has_session,
			sum(if(of.comment != "" or not isnull(of.comment), 1, 0)) as num_has_comment
		from `tabOtto Feedback` as of
		where
			1=1
			{where_clause}
		group by {group_by}
		order by of.creation desc
	"""

	data: list[list[Any]] = frappe.db.sql(query, values, as_list=True, debug=True) or []  # type: ignore
	return data
