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
					const link = frappe.utils.get_form_link("Otto Session", r.message);

					frappe.msgprint(
						`Retrying with session <a href="${link}" target="_blank">${r.message}</a>.`,
						__("Retrying")
					);
					frm.reload_doc();
					frm.refresh();
				},
			});
		}

		function resume() {
			frappe.call({
				method: "enqueue_resume",
				doc: frm.doc,
			});
		}

		function show_pending() {
			frappe.call({
				method: "get_permission_map",
				args: { only_pending: true },
				doc: frm.doc,
				callback(r) {
					frappe.msgprint(
						`<pre>${JSON.stringify(r.message || "No stats", null, 2)}</pre>`,
						__("Stats")
					);
				},
			});
		}

		if (frm.doc.status === "Failure") {
			frm.add_custom_button(__("Retry"), retry);
		}

		if (frm.doc.status === "Waiting") {
			frm.add_custom_button(__("Resume"), resume, __("Actions"));
			frm.add_custom_button(__("Show Pending"), show_pending, __("Actions"));
		}

		frm.add_web_link(`/otto_feedback?session=${frm.doc.session}`, __("Give Feedback"));
		frm.add_web_link(
			`/app/view-otto-session/${frm.doc.session}`,
			__("Open in Session Viewer")
		);
	},
});
