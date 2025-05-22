// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Otto Task", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Otto Task", {
	refresh(frm) {
		if (frm.doc.target && frm.doc.get_context) {
			frm.add_custom_button(__("Test Get Context"), () => {
				const dialog = new frappe.ui.Dialog({
					title: __("Test Get Context"),
					fields: [
						{
							fieldname: "message",
							fieldtype: "HTML",
							options: `<div>
								Execute the <code>get_context</code> function with selected document and event as <code>"Manual"</code> and view the output.
							</div>`,
						},
						{
							fieldname: "doc_name",
							label: __("Document"),
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
		}
	},
});
