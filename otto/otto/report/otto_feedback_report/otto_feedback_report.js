// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.query_reports["Otto Feedback Report"] = {
	filters: [
		{
			fieldname: "based_on",
			label: __("Based On"),
			fieldtype: "Select",
			default: "Duration",
			options: [
				{
					label: __("Period"),
					value: "Period",
				},
				{
					label: __("Duration"),
					value: "Duration",
				},
			],
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Datetime",
			depends_on: "eval:doc.based_on === 'Period'",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Datetime",
			depends_on: "eval:doc.based_on === 'Period'",
		},
		{
			fieldname: "duration",
			label: __("Duration"),
			fieldtype: "Int",
			default: 16,
			depends_on: "eval:doc.based_on === 'Duration'",
		},
		{
			fieldname: "span",
			label: __("Span"),
			fieldtype: "Select",
			default: "Week",
			options: [
				{
					label: __("Weeks"),
					value: "Week",
				},
				{
					label: __("Months"),
					value: "Month",
				},
				{
					label: __("Quarters"),
					value: "Quarter",
				},
				{
					label: __("Half-Years"),
					value: "Half-Year",
				},
				{
					label: __("Years"),
					value: "Year",
				},
			],
			depends_on: "eval:doc.based_on === 'Duration'",
		},
		{
			fieldname: "periodicity",
			label: __("Periodicity"),
			fieldtype: "Select",
			default: "Weekly",
			options: [
				{
					label: __("Weekly"),
					value: "Weekly",
				},
				{
					label: __("Monthly"),
					value: "Monthly",
				},
				{
					label: __("Quarterly"),
					value: "Quarterly",
				},
				{
					label: __("Half-Yearly"),
					value: "Half-Yearly",
				},
				{
					label: __("Yearly"),
					value: "Yearly",
				},
			],
			depends_on: "eval:doc.based_on === 'Period'",
		},
	],
};
