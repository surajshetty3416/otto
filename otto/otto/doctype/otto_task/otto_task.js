// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Task", {
	refresh(frm) {
		const { no_target } = frm.doc;
		const filter_cb = ({ fieldname }) => (no_target ? fieldname !== "target" : true);
		function execute_task() {
			const run_dialog = new frappe.ui.Dialog({
				title: __("Execute Task"),
				fields: [
					{
						fieldname: "message",
						fieldtype: "HTML",
						options: `<div>Manually enqueue task execution with selected params.</div>`,
					},
					{
						fieldname: "spacer",
						fieldtype: "HTML",
						options: `<br>`,
					},
					{
						fieldname: "target",
						label: __("Target Doc"),
						fieldtype: "Link",
						options: frm.doc.target_doctype,
						reqd: 1,
					},
					{
						fieldname: "llm",
						label: __("LLM"),
						fieldtype: "Link",
						options: "Otto LLM",
						link_filters: '[["Otto LLM","enabled","=",1]]',
						default: frm.doc.llm,
						reqd: 1,
					},
					{
						fieldname: "reasoning_effort",
						label: __("Reasoning Effort"),
						fieldtype: "Select",
						default: frm.doc.reasoning_effort,
						options: ["None", "Low", "Medium", "High"],
						description: __("Valid only if model supports reasoning"),
					},
				].filter(filter_cb),
				primary_action_label: __("Run"),
				primary_action(values) {
					frappe.call({
						method: "execute_task",
						doc: frm.doc,
						args: {
							target: no_target ? null : values.target,
							llm: values.llm || frm.doc.llm,
							reasoning_effort: values.reasoning_effort,
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
		}

		function test_get_context() {
			const dialog = new frappe.ui.Dialog({
				title: __("Test Get Context"),
				fields: [
					{
						fieldname: "message",
						fieldtype: "HTML",
						options: `<div>Execute <code>get_context</code> with event as Manual and display output.</div>`,
					},
					{
						fieldname: "spacer",
						fieldtype: "HTML",
						options: `<br>`,
					},
					{
						fieldname: "target",
						label: __("Target Doc"),
						fieldtype: "Link",
						options: frm.doc.target_doctype,
						reqd: 1,
					},
					{
						description: "View context as content passed to LLM",
						fieldname: "as_content",
						label: __("As Content"),
						fieldtype: "Check",
						default: 0,
					},
				].filter(filter_cb),
				primary_action_label: __("Test"),
				primary_action(values) {
					frappe.call({
						method: "test_get_context",
						doc: frm.doc,
						args: {
							target: no_target ? null : values.target,
							as_content: values.as_content,
						},
						callback: function (r) {
							let message = r.message;
							if (typeof message !== "string" && message.length > 0) {
								message = frappe.utils.escape_html(
									JSON.stringify(message, null, 2)
								);
							}

							if (message) frappe.msgprint(`<pre>${message}</pre>`, __("Context"));
							else frappe.msgprint(`No context`, __("Context"));
						},
					});
					dialog.hide();
				},
			});
			dialog.show();
		}

		function list_tools() {
			frappe.call({
				method: "list_tools",
				doc: frm.doc,
				callback: function (r) {
					frappe.msgprint(
						`<pre>${JSON.stringify(r.message, null, 2)}</pre>`,
						__("Tools")
					);
				},
			});
		}

		frm.add_custom_button("Execute Task", execute_task);
		frm.add_custom_button("Test Get Context", test_get_context, "Utilities");
		frm.add_custom_button("List Tool Schemas", list_tools, "Utilities");

		frappe.ui.keys.add_shortcut({ shortcut: "shift+e", action: execute_task, page: frm.page });
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+c",
			action: test_get_context,
			page: frm.page,
		});
		frappe.ui.keys.add_shortcut({ shortcut: "shift+l", action: list_tools, page: frm.page });
	},
});
