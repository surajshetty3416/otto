export const link_icon = frappe.utils.icon("es-line-arrow-up-right", "xs");

export function get_stats(execution) {
	const stats = {
		cost: 0,
		total_input_tokens: 0,
		total_output_tokens: 0,
		max_input_tokens: 0,
		max_output_tokens: 0,
		duration: 0,
		start: new Date(99999999999999),
		end: new Date(0),
		llm_calls: Object.values(execution.items).length - 1,
		tool_calls: {},
		tools: {},
	};

	for (const item of Object.values(execution.items)) {
		stats.cost += item.meta.cost || 0;
		stats.total_input_tokens += item.meta.input_tokens || 0;
		stats.total_output_tokens += item.meta.output_tokens || 0;

		if ((item.meta.input_tokens || 0) > stats.max_input_tokens) {
			stats.max_input_tokens = item.meta.input_tokens;
		}
		if ((item.meta.output_tokens || 0) > stats.max_output_tokens) {
			stats.max_output_tokens = item.meta.output_tokens;
		}

		const start = new Date((item.meta.start_time || item.meta.timestamp) * 1000);
		const end = new Date((item.meta.end_time || item.meta.timestamp) * 1000);

		if (start.valueOf() < stats.start.valueOf()) {
			stats.start = start;
		}

		if (end.valueOf() > stats.end.valueOf()) {
			stats.end = new Date(end);
		}

		for (const content of item.content) {
			if (content.type != "tool_use") continue;
			const tool = (stats.tools[content.name] ??= {
				called_count: 0,
				empty_result_count: 0,
				error_count: 0,
			});
			tool.called_count++;

			const { result, status } = content;
			if (result === null || result === "null" || result === "[]" || result === "{}")
				tool.empty_result_count++;

			if (
				status === "error" ||
				(typeof result === "string" &&
					(result.includes("Error") || result.includes("error")))
			)
				tool.error_count++;
		}
	}

	stats.duration = (stats.end.valueOf() - stats.start.valueOf()) / 1000;

	return stats;
}

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
