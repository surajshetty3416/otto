// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Task", {
	refresh(frm) {
		if (!frm.doc.target || !frm.doc.get_context) return;

		// Test Get Context
		frm.add_custom_button(__("Test Get Context"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Test Get Context"),
				fields: [
					{
						fieldname: "message",
						fieldtype: "HTML",
						options: `<div>Execute <code>get_context</code> with selected doc (with event as Manual) and display output.</div>`,
					},
					{
						fieldname: "spacer",
						fieldtype: "HTML",
						options: `<br>`,
					},
					{
						fieldname: "doc_name",
						label: __("Target Doc"),
						fieldtype: "Link",
						options: frm.doc.target,
						reqd: 1,
					},
				],
				primary_action_label: __("Test"),
				primary_action(values) {
					frappe.call({
						method: "test_get_context",
						doc: frm.doc,
						args: {
							name: values.doc_name,
						},
						callback: function (r) {
							if (r.message)
								frappe.msgprint(`<pre>${r.message}</pre>`, __("Context"));
							else frappe.msgprint(`No context`, __("Context"));
						},
					});
					dialog.hide();
				},
			});
			dialog.show();
		});

		// Run Task Execution
		frm.add_custom_button(__("Run Task Execution"), () => {
			const run_dialog = new frappe.ui.Dialog({
				title: __("Run Task Execution"),
				fields: [
					{
						fieldname: "message",
						fieldtype: "HTML",
						options: `<div>Manually enqueue task execution for the selected doc.</div>`,
					},
					{
						fieldname: "spacer",
						fieldtype: "HTML",
						options: `<br>`,
					},
					{
						fieldname: "doc_name",
						label: __("Target Doc"),
						fieldtype: "Link",
						options: frm.doc.target,
						reqd: 1,
					},
				],
				primary_action_label: __("Run"),
				primary_action(values) {
					frappe.call({
						method: "run_task_execution",
						doc: frm.doc,
						args: {
							target_doctype: values.doc_name,
						},
						callback: function (r) {
							if (r.message) {
								const link = frappe.utils.get_form_link(
									"Otto Execution",
									r.message
								);

								frappe.msgprint(
									`Execution <a href="${link}" target="_blank">${r.message}</a> created.`,
									__("Execution Created")
								);
							} else {
								frappe.msgprint(__("No execution was created."), __("Execution"));
							}
						},
					});
					run_dialog.hide();
				},
			});
			run_dialog.show();
		});
	},
});
