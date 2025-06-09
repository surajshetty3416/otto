// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto Execution", {
	refresh(frm) {
		function get_stats() {
			frappe.call({
				method: "get_stats",
				doc: frm.doc,
				callback(r) {
					frappe.msgprint(
						`<pre>${JSON.stringify(r.message, null, 2)}</pre>`,
						__("Stats")
					);
				},
			});
		}
		frm.add_custom_button(__("View Stats"), get_stats);

		frm.add_custom_button(__("Open in Execution Viewer"), () => {
			// frappe.set_route("view-otto-execution", {
			// 	executions: JSON.stringify([frm.doc.name]),
			// });
			frappe.set_route("view-otto-execution", frm.doc.name);
		});

		if (frm.doc.execution) prettify_execution(frm);
	},
});

function prettify_execution(frm) {
	const display_wrapper = get_display_wrapper(frm);

	try {
		const execution = JSON.parse(frm.doc.execution);
		if (!validate_execution(execution, display_wrapper)) return;

		const execution_area = $("<div>").appendTo(display_wrapper);
		execution_area.html(frappe.render_template("otto_execution", {}));
		render_execution_flow(execution, execution_area.find(".execution-items"));
	} catch (e) {
		console.error("Error parsing or rendering Otto Execution data:", e);
		display_wrapper.html(
			'<p class="text-danger">Error displaying execution. Check console.</p>'
		);
	}
}

function validate_execution(execution, display_wrapper) {
	if (!execution || !execution.items) {
		display_wrapper.html('<p class="text-muted">No execution items to display.</p>');
		return false;
	}

	if (typeof execution.items !== "object" || !execution.first) {
		display_wrapper.html(
			'<p class="text-warning">Execution data is incomplete or malformed.</p>'
		);
		return false;
	}

	return true;
}

function render_execution_flow(exchange, container) {
	container.empty();

	let currentItemId = exchange.first;
	const visitedItems = new Set();
	let iteration = 0;
	const maxIterations = Object.keys(exchange.items).length + 10; // Safety break

	while (currentItemId && !visitedItems.has(currentItemId) && iteration < maxIterations) {
		const item = exchange.items[currentItemId];
		if (!item) {
			container.append(
				`<p class="text-danger">Error: Referenced item ID <code>${currentItemId}</code> not found. Execution flow may be incomplete.</p>`
			);
			return;
		}

		visitedItems.add(currentItemId);
		iteration++;

		const itemElement = $('<div class="execution-item"></div>');
		itemElement.addClass(`role-${item.meta.role}`);

		// Header
		const itemHeader = $('<div class="item-header"></div>');
		const role = item.meta.role === "user" ? "system" : "llm";
		const timestamp = new Date(item.meta.timestamp * 1000).toISOString().replace("T", " ");
		itemHeader.append(
			`<span class="item-role">${role}</span>`,
			`
			<div class="item-header-meta">
				<span title="ID: ${item.id}">${item.id.slice(0, 10)}</span> ·
				<span title="Timestamp: ${timestamp}">${timestamp}</span> ·
				<span class="item-index" title="Index: ${iteration}">#${iteration}</span>
			<div>
			`
		);
		itemElement.append(itemHeader);

		// Meta
		if (item.meta.role === "agent") {
			const metaElement = $('<div class="item-meta"></div>');
			metaElement.append(
				`<div><strong>Cost:</strong> $${item.meta.cost.toFixed(6)}</div>`,
				`<div><strong>Input:</strong> ${item.meta.input_tokens} tokens</div>`,
				`<div><strong>Output:</strong> ${item.meta.output_tokens} tokens</div>`,
				`<div><strong>Model:</strong> <code>${item.meta.model}</code></div>`,
				`<div><strong>End Reason:</strong> <code>${item.meta.end_reason}</code></div>`
			);
			itemElement.append(metaElement);
		}

		// Content
		if (item.content && Array.isArray(item.content)) {
			const contentList = $('<ul class="item-content-list"></ul>');
			item.content.forEach((content) => {
				const contentElement = $('<li class="item-content"></li>');
				contentElement.addClass(`content-${content.type}`);
				const contentHtml = get_content_html(content);
				contentElement.html(contentHtml);
				contentList.append(contentElement);
			});

			itemElement.append(contentList);
		}
		container.append(itemElement);

		if (item.next && item.next.length > 0) {
			const nextIndex = typeof item.selected_next === "number" ? item.selected_next : 0;
			if (nextIndex >= 0 && nextIndex < item.next.length) {
				currentItemId = item.next[nextIndex];
			} else {
				console.warn(
					`Invalid selected_next index (${nextIndex}) for item ${item.id}. Stopping.`
				);
				currentItemId = null;
			}
		} else {
			currentItemId = null;
		}
	}

	if (iteration >= maxIterations && currentItemId) {
		container.append(
			'<p class="text-danger">Stopped rendering due to potential infinite loop or very long chain of execution items.</p>'
		);
	}
}

function get_content_html(content) {
	if (content.type === "text") {
		return `<div class="content-container">
			<strong>Text:</strong>
			<div class="content-value">${escapeHtml(content.text)}</div>
		</div>`;
	}

	if (content.type === "thinking") {
		return `<div class="content-container">
			<strong>Thinking:</strong>
			<div class="content-value">${escapeHtml(content.text)}</div>
		</div>`;
	}

	if (content.type === "tool_use") {
		const name = escapeHtml(content.name);
		const id = escapeHtml(content.id);
		const status = escapeHtml(content.status);

		const tool_header = `<div class="tool-header content-container">
				<code title="Tool: ${name} (ID: ${id})" class="tool-name">${name}</code>
				<div title="Status: ${status}" class="tool-status tool-status-${status}">${status}</div>
			</div>`;

		const tool_args = `<div class="tool-content">
				<strong>Args:</strong>
				<pre class="tool-args content-value">${escapeHtml(JSON.stringify(content.args, null, 2))}</pre>
			</div>`;

		let tool_result = "";
		if (content.result) {
			let result = escapeHtml(String(content.result));
			try {
				const parsedResult = JSON.parse(content.result);
				result = escapeHtml(JSON.stringify(parsedResult, null, 2));
			} catch {}

			tool_result = `<div class="content-container">
				<strong>Result:</strong>
				<pre class="tool-result content-value">${result}</pre>
			</div>`;
		}

		return `<div class="multi-content-value">
			${tool_header}
			${tool_args}
			${tool_result}
		</div>`;
	}

	if (content.type === "image") {
		let img_tag = "";
		if (content.data) {
			img_tag += `<img src="${content.data}" alt="Image content (embedded)">`;
		} else if (content.url) {
			img_tag += `<img src="${encodeURI(content.url)}" alt="Image content">`;
		}

		return `<div class="content-container">
			<strong>Image:</strong>
			<div class="content-value">${img_tag}</div>
		</div>`;
	}

	if (content.type === "file") {
		return `<div class="content-container">
			<strong>File:</strong>
			<div class="content-value">
				<a href="${content.data}" download="${escapeHtml(content.name)}">${escapeHtml(content.name)}</a>
			</div>
		</div>`;
	}

	return `<div class="content-container">
		<strong>Unknown content type: ${escapeHtml(content.type)}</strong>
		<div class="content-value">
			<pre>${escapeHtml(JSON.stringify(content, null, 2))}</pre>
		</div>
	</div>`;
}

function escapeHtml(unsafe) {
	if (unsafe === null || unsafe === undefined) return "";
	return String(unsafe)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#039;");
}

function get_display_wrapper(frm) {
	const execution_field = frm.fields_dict.execution; // Use 'execution' field wrapper
	if (!execution_field?.wrapper) {
		console.error("Could not find a suitable wrapper to display formatted execution.");
		return null;
	}

	// Remove existing formatted display if it exists
	$(".otto-execution-formatted-display").remove();
	$(".execution-note").remove();

	// Create a new div for the formatted display
	const display_wrapper = $("<div>")
		.addClass("otto-execution-formatted-display")
		.insertBefore(execution_field.wrapper);

	// Add note about dedicated display field
	const note = $(
		'<p class="execution-note text-muted small">Formatted view of the Execution.</p>'
	);
	display_wrapper.parent().prepend(note); // Prepend to the parent of the display_wrapper, which should be the same parent as execution_field.wrapper

	return display_wrapper;
}
