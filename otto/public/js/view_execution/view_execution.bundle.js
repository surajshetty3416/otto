import { createApp } from "vue";
import ContainerVue from "./Container.vue";
import { prompt_for_execution } from "./selection";

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
			prompt_for_execution(this.$wrapper);
		}
	}

	setup_page_actions() {
		// clear actions
		this.page.clear_actions();
		this.page.clear_menu();
		this.page.clear_custom_actions();

		this.reset_changes_btn = this.page.add_button(__("Select"), () => {
			prompt_for_execution(this.$wrapper);
		});
	}

	setup_app() {
		const app = createApp(ContainerVue, {
			execution: this.execution,
			// executions: this.executions,
		});

		this.$view_execution = app.mount(this.$wrapper.get(0));
	}
}

frappe.provide("frappe.ui");
frappe.ui.ExecutionViewer = ExecutionViewer;
export default ExecutionViewer;
