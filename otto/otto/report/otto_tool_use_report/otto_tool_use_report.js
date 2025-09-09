// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.query_reports["Otto Tool Use Report"] = {
	filters: [
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
		},
	],
};
