// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Execution", {
	refresh(frm) {
		if (!frm.doc.session) return;

		function retry() {
			frappe.call({
				method: "retry",
				doc: frm.doc,
				callback(r) {
					frappe.msgprint(r.message, __("Retry"));
					frm.reload_doc();
					frm.refresh();
				},
			});
		}

		function open_in_session_viewer() {
			frappe.set_route("view-otto-session", frm.doc.session);
		}

		frm.add_custom_button(__("Open in Session Viewer"), open_in_session_viewer);
		if (frm.doc.status === "Failure") {
			frm.add_custom_button(__("Retry"), retry);
		}
	},
});
