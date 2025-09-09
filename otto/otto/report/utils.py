import frappe.utils


def set_periodicity(filters: dict):
	if filters.get("based_on") == "Period":
		return

	to_date = frappe.utils.now_datetime()

	filters["periodicity"] = filters.get("span", "Week") + "ly"
	filters["to_date"] = to_date

	duration = filters.get("duration", 4)

	if filters.get("span") == "Week":
		filters["from_date"] = frappe.utils.add_days(to_date, -duration * 7)

	elif filters.get("span") == "Month":
		filters["from_date"] = frappe.utils.add_months(to_date, -duration)

	elif filters.get("span") == "Quarter":
		filters["from_date"] = frappe.utils.add_months(to_date, -duration * 3)

	elif filters.get("span") == "Half-Year":
		filters["from_date"] = frappe.utils.add_months(to_date, -duration * 6)

	else:
		filters["from_date"] = frappe.utils.add_years(to_date, -duration)


def get_group_by_and_period(filters: dict, table: str):
	periodicity = filters.get("periodicity", "Weekly")
	if periodicity == "Weekly":
		group_by = f"YEARWEEK({table}.creation, 1)"
		period = f"DATE_FORMAT({table}.creation, '%%Y-W%%u')"
		return group_by, period

	if periodicity == "Monthly":
		group_by = f"YEAR({table}.creation), MONTH({table}.creation)"
		period = f"DATE_FORMAT({table}.creation, '%%Y-%%m')"
		return group_by, period

	if periodicity == "Quarterly":
		group_by = f"YEAR({table}.creation), QUARTER({table}.creation)"
		period = f"CONCAT(YEAR({table}.creation), '-Q', QUARTER({table}.creation))"
		return group_by, period

	if periodicity == "Half-Yearly":
		group_by = f"YEAR({table}.creation), CASE WHEN MONTH({table}.creation) <= 6 THEN 1 ELSE 2 END"
		period = (
			f"CONCAT(YEAR({table}.creation), '-H', CASE WHEN MONTH({table}.creation) <= 6 THEN 1 ELSE 2 END)"
		)
		return group_by, period

	if periodicity == "Yearly":
		group_by = f"YEAR({table}.creation)"
		period = f"YEAR({table}.creation)"
		return group_by, period

	group_by = "1"
	period = "'All'"
	return group_by, period
