import { createApp } from "vue";
import ViewExecutionVue from "./ViewExecution.vue";

class ViewExecution {
	constructor({ wrapper, page, execution }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		// this.page.set_indicator("Sigma", "violet");
		this.execution = execution;

		// this.page.add_field({
		// 	fieldname: "execution",
		// 	fieldtype: "Link",
		// 	label: "Execution",
		// 	options: "Otto Execution",
		// 	read_only: 1,
		// });

		this.init();
	}

	init() {
		this.page.set_title(__("Viewing Execution"));
		this.setup_page_actions();
		this.setup_app();
	}

	setup_page_actions() {
		// clear actions
		this.page.clear_actions();
		this.page.clear_menu();
		this.page.clear_custom_actions();

		// setup page actions
		// this.primary_btn = this.page.set_primary_action(__("Save"), () =>
		// 	this.store.save_changes()
		// );

		// this.reset_changes_btn = this.page.add_button(__("Go to Execution"), () => {
		// 	frappe.set_route("Form", "Otto Execution", this.execution);
		// });

		// this.go_to_doctype_btn = this.page.add_menu_item(__("Go to Execution"), () =>
		// 	frappe.set_route("Form", "Otto Execution", this.execution)
		// );
	}

	setup_app() {
		const app = createApp(ViewExecutionVue, {
			executionName: this.execution,
		});

		this.$view_execution = app.mount(this.$wrapper.get(0));
	}
}

frappe.provide("frappe.ui");
frappe.ui.ViewExecution = ViewExecution;
export default ViewExecution;
