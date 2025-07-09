/**
 * This file is created by creating a new Page entry using Desk, i.e. at
 * /app/page. The frappe.require line loads a built bundle of
 * otto/public/js/view_session/view_session.bundle.js
 *
 * This is a Vue app. To hot reload while development use:
 * $ npm run build -- --apps otto --watch
 *
 * In the frappe folder (check command is defined in its package.json).
 */
frappe.pages["view-otto-session"].on_page_show = (wrapper) => load_session_viewer(wrapper);
frappe.pages["view-otto-session"].on_page_load = (wrapper) => {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "View Session",
		single_column: true,
	});

	// hot reload in development
	if (frappe.boot.developer_mode) {
		frappe.hot_update = frappe.hot_update || [];
		frappe.hot_update.push(() => load_session_viewer(wrapper));
	}
};

function load_session_viewer(wrapper) {
	const $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require("view_session.bundle.js").then(() => {
		frappe.session_viewer = new frappe.ui.SessionViewer({
			wrapper: $parent,
			page: wrapper.page,
		});
	});
}
