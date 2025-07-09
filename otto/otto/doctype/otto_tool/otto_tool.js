// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Tool", {
	refresh(frm) {
		// Add JSON Schema button to display the function schema
		function view_schema() {
			frappe.call({
				method: "get_function_schema",
				doc: frm.doc,
				callback: function (r) {
					if (r.message) {
						// Format the schema as JSON with indentation
						const formattedSchema = JSON.stringify(r.message, null, 2);
						frappe.msgprint({
							title: "Function Schema",
							message: `<pre>${formattedSchema}</pre>`,
							wide: true,
						});
					}
				},
			});
		}

		function test_tool() {
			// Create fields for the dialog based on the tool's arguments
			let fields = [];
			if (frm.doc.args && frm.doc.args.length) {
				frm.doc.args.forEach((arg) => {
					fields.push({
						label: arg.arg_name,
						fieldname: arg.arg_name,
						fieldtype:
							arg.type === "string"
								? "Data"
								: arg.type === "integer"
								? "Int"
								: arg.type === "number"
								? "Float"
								: arg.type === "boolean"
								? "Check"
								: arg.type === "array"
								? "Code"
								: arg.type === "object"
								? "Code"
								: "Data",
						reqd: arg.is_required,
						description: arg.description,
					});
				});
			}

			function callTestExecute(values) {
				frappe.call({
					method: "test_tool",
					doc: frm.doc,
					args: values,
					callback: function (r) {
						if (r.message)
							frappe.msgprint(
								`<pre>${frappe.utils.escape_html(r.message)}</pre>`,
								__("Tool Session Result")
							);
						else frappe.msgprint(`No result`, __("Tool Session Result"));
					},
				});
			}

			if (fields.length === 0) {
				return callTestExecute({});
			}

			// Create and show the dialog
			let d = new frappe.ui.Dialog({
				title: "Execute Tool",
				fields: fields,
				primary_action_label: "Execute",
				primary_action(values) {
					// For array and object types, parse the JSON
					Object.keys(values).forEach((key) => {
						const arg = frm.doc.args.find((a) => a.arg_name === key);
						if (arg && (arg.type === "array" || arg.type === "object")) {
							try {
								values[key] = JSON.parse(values[key]);
							} catch (e) {
								frappe.throw(`Invalid JSON for ${key}`);
							}
						}
					});

					callTestExecute(values);
					d.hide();
				},
			});
			d.show();
		}

		frm.add_custom_button("View Schema", view_schema);
		frm.add_custom_button("Test Tool", test_tool);

		frappe.ui.keys.add_shortcut({ shortcut: "shift+v", action: view_schema, page: frm.page });
		frappe.ui.keys.add_shortcut({ shortcut: "shift+o", action: test_tool, page: frm.page });
	},
});
