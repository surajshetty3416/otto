export function show_session_dialog(sessions) {
	const selected_sessions = [];
	const dialog = new frappe.ui.Dialog({
		title: __("Select Session"),
		// title: __("Select up to 3 Sessions"),
		// primary_action_label: __("View"),
		// primary_action: () => {
		// 	if (selected_sessions.length <= 0) return;
		// 	frappe.set_route(frappe.get_route()[0], {
		// 		sessions: JSON.stringify(selected_sessions),
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
				${sessions
					.map(
						(ex) => `
					<div class="list-group-item list-group-item-action px-0 border-0" data-session-name="${
						ex.name
					}" style="cursor: pointer; ${
							ex === sessions[sessions.length - 1]
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
			const sessionName = $this.data("session-name");
			frappe.set_route("view-otto-session", sessionName);
			// const is_selected = $this.hasClass("active");

			// if (is_selected) {
			// 	$this.removeClass("active").css("background-color", "");
			// 	selected_sessions = selected_sessions.filter((name) => name !== sessionName);
			// } else {
			// 	if (selected_sessions.length < 3) {
			// 		$this.addClass("active").css("background-color", "var(--gray-100)");
			// 		selected_sessions.push(sessionName);
			// 	} else {
			// 		frappe.show_alert({
			// 			message: __("You can only select up to 3 sessions."),
			// 			indicator: "orange",
			// 		});
			// 	}
			// }

			// primary_action_btn.prop("disabled", selected_sessions.length === 0);
		});

	dialog.show();
}
