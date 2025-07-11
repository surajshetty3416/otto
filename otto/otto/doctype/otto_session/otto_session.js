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

		function open_in_session_viewer() {
			frappe.set_route("view-otto-session", frm.doc.name);
		}

		frm.add_custom_button(__("View Stats"), get_stats);
		frm.add_custom_button(__("Open in Session Viewer"), open_in_session_viewer);
	},
});
