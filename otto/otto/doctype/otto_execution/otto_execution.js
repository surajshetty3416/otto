// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Execution", {
	refresh(frm) {
		frm.add_custom_button(__("Get Stats"), () => {
			frappe.call({
				method: "get_stats",
				doc: frm.doc,
				callback: (r) => {
					frappe.msgprint(
						`<pre>${JSON.stringify(r.message, null, 2)}</pre>`,
						__("Stats")
					);
				},
			});
		});
	},
});
