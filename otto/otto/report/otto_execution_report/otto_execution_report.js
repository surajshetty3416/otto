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
	],
};
