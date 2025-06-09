export function prompt_for_execution(wrapper) {
	frappe.call({
		method: "otto.otto.doctype.otto_execution.otto_execution.get_recent_executions",
		callback: (r) => {
			if (r.message && r.message.length) {
				show_execution_dialog(r.message);
			}
		},
	});
}

export function show_execution_dialog(executions) {
	let selected_executions = [];

	const dialog = new frappe.ui.Dialog({
		title: __("Select Execution"),
		// title: __("Select up to 3 Executions"),
		// primary_action_label: __("View"),
		// primary_action: () => {
		// 	if (selected_executions.length <= 0) return;
		// 	frappe.set_route(frappe.get_route()[0], {
		// 		executions: JSON.stringify(selected_executions),
		// 	});
		// 	dialog.hide();
		// },
		secondary_action_label: __("Cancel"),
		secondary_action: () => dialog.hide(),
	});

	// const primary_action_btn = dialog.get_primary_btn();
	// primary_action_btn.prop("disabled", true);

	dialog.body.innerHTML = `
			<div class="list-group" style="max-height: 400px; overflow-y: auto; border: none; border-radius: 0;">
				${executions
					.map(
						(ex) => `
					<div class="list-group-item list-group-item-action px-0 border-0" data-execution-name="${
						ex.name
					}" style="cursor: pointer; ${
							ex === executions[executions.length - 1]
								? ""
								: "border-bottom: 1px solid var(--gray-200) !important;"
						}">
						<div class="row mx-0 align-items-center">
							<div class="col-3 text-left">
								<h6 class="mb-0">${ex.name}</h6>
							</div>
							<div class="col-3 text-left">
								<p class="mb-0 small text-muted">${ex.task_name}</p>
							</div>
							<div class="col-3 text-center">
								<p class="mb-0 small text-muted">${ex.status}</p>
							</div>
							<div class="col-3 text-right">
								<small class="text-muted">${frappe.datetime.comment_when(ex.creation)}</small>
							</div>
						</div>
					</div>
					`
					)
					.join("")}
			</div>
		`;

	$(dialog.body)
		.find(".list-group-item")
		.on("click", function (e) {
			e.preventDefault();
			const $this = $(this);
			const executionName = $this.data("execution-name");
			frappe.set_route("view-otto-execution", executionName);
			// const is_selected = $this.hasClass("active");

			// if (is_selected) {
			// 	$this.removeClass("active").css("background-color", "");
			// 	selected_executions = selected_executions.filter((name) => name !== executionName);
			// } else {
			// 	if (selected_executions.length < 3) {
			// 		$this.addClass("active").css("background-color", "var(--gray-100)");
			// 		selected_executions.push(executionName);
			// 	} else {
			// 		frappe.show_alert({
			// 			message: __("You can only select up to 3 executions."),
			// 			indicator: "orange",
			// 		});
			// 	}
			// }

			// primary_action_btn.prop("disabled", selected_executions.length === 0);
		});

	dialog.show();
}
