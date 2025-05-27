// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto LLM", {
	refresh(frm) {
		function ask() {
			const run_dialog = new frappe.ui.Dialog({
				title: __("Run Task Execution"),
				fields: [
					{
						fieldname: "message",
						fieldtype: "HTML",
						options: `<div>Test the LLM by asking it a question.</div>`,
					},
					{
						fieldname: "spacer",
						fieldtype: "HTML",
						options: `<br>`,
					},
					{
						fieldname: "query",
						label: __("Query"),
						fieldtype: "Data",
						default: "Hello, how are you?",
						reqd: 1,
					},
					{
						fieldname: "system",
						label: __("System Prompt"),
						fieldtype: "Data",
						default: "You are a helpful assistant.",
						reqd: 1,
					},
				],
				primary_action_label: __("Ask"),
				primary_action(values) {
					frappe.call({
						method: "ask",
						doc: frm.doc,
						args: {
							query: values.query,
							system: values.system,
						},
						callback(r) {
							frappe.msgprint(
								`<pre>${r?.message || "No Response"}</pre>`,
								__("Response")
							);
						},
					});
					run_dialog.hide();
				},
			});
			run_dialog.show();
		}

		frm.add_custom_button(__("Ask"), ask);
	},
});
