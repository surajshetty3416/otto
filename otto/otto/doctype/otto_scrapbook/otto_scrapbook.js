// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Scrapbook", {
	refresh(frm) {
		let content = {};
		try {
			content = JSON.parse(frm.doc.content);
		} catch {}

		const head = [...Object.keys(content)]
			.map((key) => ` <strong><code>${key}</code></strong><br><pre>${content[key]}</pre> `)
			.join("<br>");
		frm.layout.show_message(head);
	},
});
