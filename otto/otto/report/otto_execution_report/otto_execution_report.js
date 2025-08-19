// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.query_reports["Otto Execution Report"] = {
	filters: [
		{
			fieldname: "task",
			label: __("Task"),
			fieldtype: "Link",
			options: "Otto Task",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Datetime",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Datetime",
		},
		{
			fieldname: "llm",
			label: __("LLM"),
			fieldtype: "Link",
			options: "Otto LLM",
		},
		{
			fieldname: "event",
			label: __("Event"),
			fieldtype: "Select",
			default: "",
			options: [
				{
					label: __("All"),
					value: "",
				},
				{
					label: __("On Create"),
					value: "On Create",
				},
				{
					label: __("On Update"),
					value: "On Update",
				},
				{
					label: __("On Delete"),
					value: "On Delete",
				},
				{
					label: __("On Submit"),
					value: "On Submit",
				},
				{
					label: __("On Cancel"),
					value: "On Cancel",
				},
				{
					label: __("Manual"),
					value: "Manual",
				},
			],
		},
		{
			fieldname: "show_tool_counts",
			label: __("Show Tool Counts"),
			fieldtype: "Check",
			default: 0,
			depends_on: "eval:doc.task",
		},
		{
			fieldname: "show_stats",
			label: __("Show Stats"),
			fieldtype: "Check",
			default: 1,
		},
		{
			fieldname: "show_feedback",
			label: __("Show Feedback Score"),
			fieldtype: "Check",
			default: 0,
		},
	],
	onload: function (report) {
		// Set default date range to last 7 days if no dates are set
		const filters = report.get_filter_values();
		if (!filters.from_date && !filters.to_date) {
			const now = frappe.datetime.now_datetime();
			const seven_days_ago = frappe.datetime.add_days(now, -7);

			report.set_filter_value("from_date", seven_days_ago);
			report.set_filter_value("to_date", now);
		}
	},
};
