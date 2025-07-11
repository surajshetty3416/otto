export const link_icon = frappe.utils.icon("es-line-arrow-up-right", "xs");

export function get_link(doctype, name) {
	return frappe.utils.get_form_link(doctype, name);
}

export function format_date(timestamp) {
	if (typeof timestamp === "number" && timestamp < 1600000000000) {
		timestamp = timestamp * 1000;
	}

	if (!timestamp) return "N/A";
	return new Date(timestamp).toLocaleString();
}

export function format_duration(duration) {
	if (duration < 60) {
		return `${duration.toFixed(2)}s`;
	}

	return frappe.utils.get_formatted_duration(duration);
}

export function format_number(number) {
	return number.toLocaleString();
}

export function escape_html(str) {
	if (!str) return "";
	return str
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#039;");
}

export function get_icon(name, size = "xs") {
	return frappe.utils.icon(name, size);
}

export function get_chevron(show) {
	let chevron = "chevron-up";
	if (!show) chevron = "chevron-down";
	return frappe.utils.icon(chevron, "sm");
}

export function safe_stringify(obj) {
	try {
		return JSON.stringify(obj);
	} catch {
		return String(obj);
	}
}
