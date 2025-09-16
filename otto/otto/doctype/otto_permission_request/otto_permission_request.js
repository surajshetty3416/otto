// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Permission Request", {
	refresh(frm) {
		frm.arg_controls = set_arg_controls(frm);
		if (frm.doc.session) {
			frm.add_web_link(
				`/app/view-otto-session/${frm.doc.session}`,
				__("Open in Session Viewer")
			);
		}

		if (frm.doc.status !== "Pending") return;

		async function grant() {
			const override_args = get_override(frm);
			const diffed = Object.keys(override_args).map(
				(k) => `<strong>${frappe.utils.to_title_case(k)}</strong>`
			);

			if (diffed.length === 0) {
				await frm.call("grant");
				await frm.reload_doc();
				show_toast();
				return;
			}

			frappe.confirm(
				`Use updated values for ${diffed.join(", ")}?`,
				async () => {
					await frm.call("grant", { override_args });
					await frm.reload_doc();
					show_toast();
				},
				async () => {
					await frm.call("grant");
					await frm.reload_doc();
					show_toast();
				}
			);
		}

		async function deny() {
			await frm.call("deny");
			await frm.reload_doc();
			show_toast();
		}

		function show_toast() {
			const message =
				frm.doc.status === "Granted" ? "Permission granted" : "Permission denied";
			const indicator = frm.doc.status === "Granted" ? "green" : "red";
			frappe.toast({ message, indicator });
		}

		frm.page.set_primary_action(__("Grant"), grant);
		frm.add_custom_button(__("Deny"), deny);

		frappe.ui.keys.add_shortcut({ shortcut: "shift+g", action: grant, page: frm.page });
		frappe.ui.keys.add_shortcut({ shortcut: "shift+d", action: deny, page: frm.page });
	},
});

function get_override(frm) {
	const override = {};
	const args = JSON.parse(frm.doc.tool_use_args);
	for (const [key, control] of Object.entries(frm.arg_controls)) {
		const value = control.get_value();
		let arg_value = args[key];
		if (control.df.fieldtype === "JSON") {
			arg_value = JSON.stringify(arg_value);
		}

		if (arg_value === value) {
			continue;
		}

		override[key] = value;
		if (control.df.fieldtype === "JSON") {
			override[key] = JSON.parse(value);
		}
	}

	return override;
}

function set_arg_controls(frm) {
	// Use the tool_use_args field wrapper to display individual arguments
	const parent = frm.fields_dict.tool_use_args.$wrapper;
	if (!parent) return;
	parent.empty();

	const args = JSON.parse(frm.doc.tool_use_args);
	const descriptions = JSON.parse(frm.doc.descriptions || "{}");

	const controls = {};
	const entries = Object.entries(args).sort((a, b) => {
		if (a === "explanation") return -1;
		if (b === "explanation") return 1;
		return a[0].localeCompare(b[0]);
	});

	// Create form controls for each argument
	for (const [key, value] of entries) {
		const df = {
			fieldname: `tool_arg_${key}`,
			fieldtype: "Data",
			label: frappe.utils.to_title_case(key),
			description: descriptions[key],
			read_only: frm.doc.status !== "Pending",
		};

		if (key === "explanation") {
			df.description = __(
				"A short explanation of why the this tool is being called, and how it contributes to the task."
			);
			df.read_only = true;
		}

		let field_value = value;
		if (is_markdown(value)) {
			df.fieldtype = "Code";
			df.options = "Markdown";
		} else if (typeof value === "number") {
			df.fieldtype = "Float";
		} else if (typeof value !== "string") {
			field_value = JSON.stringify(value, null, 2);
			df.fieldtype = "JSON";
		}

		const control = frappe.ui.form.make_control({
			df,
			parent,
			render_input: true,
		});
		control.set_value(field_value);
		controls[key] = control;
	}

	return controls;
}

function is_markdown(value) {
	if (typeof value !== "string") return false;

	return (
		value.includes("```") ||
		value.includes("`") ||
		value.includes("\n") ||
		value.includes("# ") ||
		value.length > 100
	);
}
