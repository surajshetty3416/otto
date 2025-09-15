// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Assistant", {
	refresh(frm) {
		function get_instruction() {
			frappe.call({
				method: "get_instruction",
				doc: frm.doc,
				callback: function (r) {
					let message = r.message;
					if (typeof message !== "string") {
						message = frappe.utils.escape_html(JSON.stringify(message, null, 2));
					}

					if (message) {
						frappe.msgprint(`<pre>${message}</pre>`, __("Instruction"));
					} else {
						frappe.msgprint("No instruction", __("Instruction"));
					}
				},
			});
		}

		function test_get_context() {
			frappe.call({
				method: "run_get_context",
				doc: frm.doc,
				callback: function (r) {
					let message = r.message;
					if (typeof message !== "string") {
						message = frappe.utils.escape_html(JSON.stringify(message, null, 2));
					}

					if (message) {
						frappe.msgprint(`<pre>${message}</pre>`, __("Context"));
					} else {
						frappe.msgprint("No context", __("Context"));
					}
				},
			});
		}

		frm.add_custom_button("Get Instruction", get_instruction, "Utilities");
		frm.add_custom_button("Test Get Context", test_get_context, "Utilities");

		frappe.ui.keys.add_shortcut({
			shortcut: "shift+i",
			action: get_instruction,
			page: frm.page,
		});
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+c",
			action: test_get_context,
			page: frm.page,
		});
	},
});
