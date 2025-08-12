// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Session", {
	refresh(frm) {
		function get_stats() {
			frappe.call({
				method: "get_stats",
				doc: frm.doc,
				callback(r) {
					frappe.msgprint(
						`<pre>${JSON.stringify(r.message || "No stats", null, 2)}</pre>`,
						__("Stats")
					);
				},
			});
		}

		frm.add_custom_button(__("View Stats"), get_stats);

		frm.add_web_link(`/otto_feedback?session=${frm.doc.name}`, __("Give Feedback"));
		frm.add_web_link(`/app/view-otto-session/${frm.doc.name}`, __("Open in Session Viewer"));
	},
});
