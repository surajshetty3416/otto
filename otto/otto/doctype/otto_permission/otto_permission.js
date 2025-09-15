// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Permission", {
	refresh(frm) {
		if (frm.doc.status !== "Pending") return;

		function grant() {
			frm.call("grant").then(() => {
				frm.reload_doc();
			});
		}

		function deny() {
			frm.call("deny").then(() => {
				frm.reload_doc();
			});
		}

		frm.page.set_primary_action(__("Grant"), grant);
		frm.add_custom_button(__("Deny"), deny);

		frappe.ui.keys.add_shortcut({ shortcut: "shift+g", action: grant, page: frm.page });
		frappe.ui.keys.add_shortcut({ shortcut: "shift+d", action: deny, page: frm.page });
	},
});
