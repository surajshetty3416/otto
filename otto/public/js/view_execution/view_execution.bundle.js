import { createApp } from "vue";
import ContainerVue from "./Container.vue";

class ExecutionViewer {
	constructor({ wrapper, page, execution }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		this.execution = execution;

		this.init();
	}

	init() {
		this.page.set_title(__("Execution Viewer"));
		this.setup_page_actions();
		this.setup_app();
	}

	setup_page_actions() {
		// clear actions
		this.page.clear_actions();
		this.page.clear_menu();
		this.page.clear_custom_actions();
	}

	setup_app() {
		const app = createApp(ContainerVue, {
			executionName: this.execution,
		});

		this.$view_execution = app.mount(this.$wrapper.get(0));
	}
}

frappe.provide("frappe.ui");
frappe.ui.ExecutionViewer = ExecutionViewer;
export default ExecutionViewer;
