import { createApp, ref } from "vue";
import ContainerVue from "./Container.vue";
import { show_session_dialog } from "./selection";

class SessionViewer {
	constructor({ wrapper, page }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		// this.sessions = JSON.parse(frappe.route_options.sessions ?? "[]");
		this.session = frappe.get_route()[1];
		this.init();
	}

	init() {
		this.page.set_title(__("Session Viewer"));
		this.setup_page_actions();
		if (this.session) {
			this.setup_app();
		} else {
			this.select_session(this.$wrapper);
		}
	}

	setup_page_actions() {
		this.page.clear_actions();
		this.page.clear_menu();
		this.page.clear_custom_actions();

		this.page.add_button(__("Select"), () => this.select_session(this.$wrapper));
		this.page.add_button(__("Help"), show_help);
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+s",
			action: this.select_session,
			page: this.page,
		});
		if (!this.session) return;

		this.page.set_primary_action(__("Log Feedback"), () => feedback(this.session));
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+f",
			action: () => feedback(this.session),
			page: this.page,
		});

		const next_session = () => this.get_adjacent_session(true);
		this.page.add_menu_item(__("Next"), next_session, true, {
			shortcut: "Shift+N",
		});
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+n",
			action: next_session,
			page: this.page,
		});

		const previous_session = () => this.get_adjacent_session(false);
		this.page.add_menu_item(__("Previous"), previous_session, true, {
			shortcut: "Shift+P",
		});
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+p",
			action: previous_session,
			page: this.page,
		});

		this.page.add_menu_item(__("Help"), show_help, true, {
			shortcut: "Shift+H",
		});
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+h",
			action: show_help,
		});
	}

	select_session(wrapper) {
		frappe.call({
			method: "otto.api.session_view.get_recent_sessions",
			args: { page: 0, limit: 20 },
			callback: (r) => show_session_dialog(r.message),
		});
	}

	get_adjacent_session(next) {
		frappe.call({
			method: "otto.api.session_view.get_adjacent_session",
			args: { name: this.session, next },
			callback: (r) => {
				if (r.message) {
					this.app?.unmount();
					frappe.set_route("view-otto-session", r.message);
				} else {
					frappe.show_alert({
						message: __("No adjacent session found"),
						indicator: "orange",
					});
				}
			},
		});
	}

	setup_app() {
		this.app = createApp(ContainerVue, {
			session: this.session,
			// sessions: this.sessions,
		});

		window.app = this.app;
		this.$view_session = this.app.mount(this.$wrapper.get(0));
	}
}

frappe.provide("frappe.ui");
frappe.ui.SessionViewer = SessionViewer;
export default SessionViewer;

function show_help() {
	const shortcuts = [
		{
			name: __("Select"),
			shortcut: "Shift+S",
			description: __("Select an session to view"),
		},
		{
			name: __("Log Feedback"),
			shortcut: "Shift+F",
			description: __("Log feedback for selected session"),
		},
		{ name: __("Next"), shortcut: "Shift+N", description: __("Go to the next session") },
		{
			name: __("Previous"),
			shortcut: "Shift+P",
			description: __("Go to the previous session"),
		},
		{ name: __("Help"), shortcut: "Shift+H", description: __("Show this help dialog") },
	];

	const shortcut_rows = shortcuts
		.map(
			(s) =>
				`<tr><td>${s.name}</td><td>${s.description}</td><td style="text-align: right;"><kbd>${s.shortcut}</kbd></td></tr>`
		)
		.join("");

	const html = `
			<p>
				Use the Session Viewer to view task sessions and provide feedback.
			</p>
			<table class="table" style="margin-bottom: 0;">
				<thead>
					<tr>
						<th>${__("Function")}</th>
						<th>${__("Description")}</th>
						<th style="text-align: right;">${__("Shortcut")}</th>
					</tr>
				</thead>
				<tbody>
					${shortcut_rows}
				</tbody>
			</table>
		`;

	frappe.msgprint({
		title: __("Help"),
		message: html,
		wide: true,
	});
}

function feedback(session) {
	let value = 0;
	const dialog = new frappe.ui.Dialog({
		title: __("Provide Feedback for {0}", [session]),
		fields: [
			{ fieldname: "thumb_buttons", fieldtype: "HTML" },
			{ fieldname: "spacer", fieldtype: "HTML", options: "<br>" },
			{
				label: __("Comment"),
				fieldname: "comment",
				fieldtype: "Small Text",
			},
		],
		primary_action_label: __("Log"),
		primary_action: ({ comment }) => {
			if (value === 0 && !comment) {
				frappe.show_alert({
					message: __("Please provide a comment or select a thumb"),
					indicator: "orange",
				});
				return;
			}

			frappe.db.insert({
				doctype: "Otto Feedback",
				session,
				value,
				comment,
			});

			dialog.hide();
			frappe.show_alert({
				message: __("Feedback logged for {0}", [session]),
				indicator: "green",
			});
		},

		secondary_action_label: __("Cancel"),
		secondary_action: () => dialog.hide(),
	});

	const field = dialog.get_field("thumb_buttons");
	const thumbs_html = `
			<p>Was Otto helpful?</p>
			<div class="btn-group" role="group">
				<button type="button" class="btn btn-default"  name="up">
					&#128077;
				</button>
				<button type="button" class="btn btn-default" name="down">
					&#128078;
				</button>
			</div>
		`;
	$(field.wrapper).html(thumbs_html);

	$(field.wrapper)
		.find(".btn")
		.on("click", (e) => {
			const button = $(e.currentTarget);
			const name = button.attr("name");
			$(field.wrapper).find(".btn").removeClass("btn-primary").addClass("btn-default");

			if ((name === "up" && value === 1) || (name === "down" && value === -1)) {
				value = 0;
			} else if (name === "up") {
				value = 1;
				button.removeClass("btn-default").addClass("btn-primary");
			} else if (name === "down") {
				value = -1;
				button.removeClass("btn-default").addClass("btn-primary");
			}
		});

	dialog.show();
}
