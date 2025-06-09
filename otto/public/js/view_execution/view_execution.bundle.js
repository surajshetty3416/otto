import { createApp, ref } from "vue";
import ContainerVue from "./Container.vue";
import { show_execution_dialog } from "./selection";

class ExecutionViewer {
	constructor({ wrapper, page }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		// this.executions = JSON.parse(frappe.route_options.executions ?? "[]");
		this.execution = frappe.get_route()[1];
		this.init();
	}

	init() {
		this.page.set_title(__("Execution Viewer"));
		this.setup_page_actions();
		if (this.execution) {
			this.setup_app();
		} else {
			this.select_execution(this.$wrapper);
		}
	}

	setup_page_actions() {
		this.page.clear_actions();
		this.page.clear_menu();
		this.page.clear_custom_actions();

		this.page.add_button(__("Select"), () => this.select_execution(this.$wrapper));
		this.page.add_button(__("Help"), show_help);
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+s",
			action: this.select_execution,
			page: this.page,
		});
		if (!this.execution) return;

		this.page.set_primary_action(__("Feedback"), this.feedback);
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+f",
			action: this.feedback,
			page: this.page,
		});

		const next_execution = () => this.get_adjacent_execution(true);
		this.page.add_menu_item(__("Next"), next_execution, true, {
			shortcut: "Shift+N",
		});
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+n",
			action: next_execution,
			page: this.page,
		});

		const previous_execution = () => this.get_adjacent_execution(false);
		this.page.add_menu_item(__("Previous"), previous_execution, true, {
			shortcut: "Shift+P",
		});
		frappe.ui.keys.add_shortcut({
			shortcut: "shift+p",
			action: previous_execution,
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

	select_execution(wrapper) {
		frappe.call({
			method: "otto.otto.doctype.otto_execution.otto_execution.get_recent_executions",
			callback: (r) => show_execution_dialog(r.message),
		});
	}

	feedback() {
		console.log("feedback");
	}

	get_adjacent_execution(next) {
		frappe.call({
			method: "otto.otto.doctype.otto_execution.otto_execution.get_adjacent_execution",
			args: { name: this.execution, next },
			callback: (r) => {
				if (r.message) {
					this.app?.unmount();
					frappe.set_route("view-otto-execution", r.message);
				} else {
					frappe.show_alert({
						message: __("No adjacent execution found"),
						indicator: "orange",
					});
				}
			},
		});
	}

	setup_app() {
		this.app = createApp(ContainerVue, {
			execution: this.execution,
			// executions: this.executions,
		});

		window.app = this.app;
		this.$view_execution = this.app.mount(this.$wrapper.get(0));
	}
}

frappe.provide("frappe.ui");
frappe.ui.ExecutionViewer = ExecutionViewer;
export default ExecutionViewer;

function show_help() {
	const shortcuts = [
		{
			name: __("Select"),
			shortcut: "Shift+S",
			description: __("Select an execution to view"),
		},
		{
			name: __("Feedback"),
			shortcut: "Shift+F",
			description: __("Provide feedback on the execution"),
		},
		{ name: __("Next"), shortcut: "Shift+N", description: __("Go to the next execution") },
		{
			name: __("Previous"),
			shortcut: "Shift+P",
			description: __("Go to the previous execution"),
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
				Use the Execution Viewer to view task executions and provide feedback.
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
