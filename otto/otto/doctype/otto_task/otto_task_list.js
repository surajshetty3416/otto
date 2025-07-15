frappe.listview_settings["Otto Task"] = {
	onload(listview) {
		// listview.page.add_inner_button("Import Task", import_task);
	},
};

function import_task() {
	const input = document.createElement("input");
	input.type = "file";
	input.accept = ".json";

	input.onchange = function (e) {
		const file = e.target.files[0];
		const reader = new FileReader();

		reader.onload = function (e) {
			try {
				const data = JSON.parse(e.target.result);
				frappe.call({
					method: "otto.otto.doctype.otto_task.otto_task.import_task",
					args: { data },
					callback: function (r) {
						if (!r.message) {
							frappe.msgprint(__("Import failed"), __("Error"));
							return;
						}

						const link = frappe.utils.get_form_link("Otto Task", r.message);
						frappe.msgprint(
							`Task <b>${data.title}</b> successfully imported. <a href="${link}" target="_blank">View Task</a>`,
							__("Import Successful")
						);
					},
				});
			} catch (error) {
				frappe.msgprint(__("Invalid JSON file"), __("Error"));
			}
		};

		reader.readAsText(file);
	};

	input.click();
}
