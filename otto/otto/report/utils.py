import frappe.utils


def set_periodicity(filters: dict):
	if filters.get("based_on") == "Period":
		return

	filters["periodicity"] = filters.get("span", "Week") + "ly"
	filters["to_date"] = frappe.utils.now_datetime()
	filters["from_date"] = frappe.utils.add_days(filters["to_date"], -filters.get("duration", 4) * 7)
