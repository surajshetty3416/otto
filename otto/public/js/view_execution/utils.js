export function calculateStats(execution) {
	const stats = {
		cost: 0,
		total_input_tokens: 0,
		total_output_tokens: 0,
		max_input_tokens: 0,
		max_output_tokens: 0,
		duration: 0,
		start: new Date(99999999999999),
		end: new Date(0),
		tool_calls: {},
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
			stats.tool_calls[content.name] = (stats.tool_calls[content.name] || 0) + 1;
		}
	}

	stats.duration = stats.end.valueOf() - stats.start.valueOf();

	return stats;
}

export function formatDate(datetimeStr) {
	if (!datetimeStr) return "N/A";
	return new Date(datetimeStr).toLocaleString();
}
