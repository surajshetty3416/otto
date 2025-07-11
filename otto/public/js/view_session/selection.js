export function show_session_dialog(sessions) {
	const limit = 20;
	const dialog = new frappe.ui.Dialog({
		title: __("Select Session"),
		secondary_action_label: __("More"),
		secondary_action: () => {
			frappe.call({
				method: "otto.otto.page.view_otto_session.session_view.get_recent_sessions",
				args: { page: Math.ceil(sessions.length / limit), limit },
				callback: (r) => {
					if (r.message.length === 0) return;
					sessions = sessions.concat(r.message);
					render_body();
				},
			});
		},
	});

	function render_body() {
		dialog.body.innerHTML = `
			<div class="list-group" style="max-height: 400px; overflow-y: auto; border: none; border-radius: 0;">
				${sessions
					.map(
						(ex, i) => `
					<div class="list-group-item list-group-item-action px-0 border-0" data-session-name="${
						ex.name
					}" style="cursor: pointer; ${
							ex === sessions[sessions.length - 1]
								? ""
								: "border-bottom: 1px solid var(--gray-200) !important;"
						}">
						<div class="row mx-0 align-items-center">
							<div class="col-1">${i + 1}.</div>
							<div class="col text-left">
								<h6 class="mb-0">${ex.name}</h6>
							</div>
							<div class="col text-left">
								<p class="mb-0 small text-muted">${ex.task_name}</p>
							</div>
							<div class="col text-center">
								<p class="mb-0 small text-muted">${ex.status}</p>
							</div>
							<div class="col text-right">
								<small class="text-muted">${frappe.datetime.comment_when(ex.creation)}</small>
							</div>
						</div>
					</div>
					`
					)
					.join("")}
			</div>
		`;
	}

	render_body();
	$(dialog.body)
		.find(".list-group-item")
		.on("click", function (e) {
			e.preventDefault();
			const $this = $(this);
			const sessionName = $this.data("session-name");
			frappe.set_route("view-otto-session", sessionName);
		});

	dialog.show();
}
