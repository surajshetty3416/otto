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
		frm.add_custom_button(__("Get Stats"), get_stats);

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
			console.warn(
				`Item with ID ${currentItemId} not found in exchange.items. Stopping render at this point.`
			);
			container.append(
				`<p class="text-danger">Error: Referenced item ID <code>${currentItemId}</code> not found. Execution flow may be incomplete.</p>`
			);
			break;
		}

		visitedItems.add(currentItemId);
		iteration++;

		const itemElement = $('<div class="execution-item"></div>');
		itemElement.addClass(`role-${item.meta.role}`);

		const itemHeader = $('<div class="item-header"></div>');
		itemHeader.append(`<span class="item-role">${item.meta.role}</span>`);
		itemHeader.append(`<span class="item-id">ID: ${item.id}</span>`);
		itemElement.append(itemHeader);

		const metaElement = $('<div class="item-meta"></div>');
		metaElement.append(
			`<div><strong>Model:</strong> <code>${item.meta.model || "N/A (Human)"}</code></div>`
		);
		metaElement.append(
			`<div><strong>Timestamp:</strong> ${new Date(
				item.meta.timestamp * 1000
			).toLocaleString()}</div>`
		);
		if (
			typeof item.meta.input_tokens === "number" &&
			typeof item.meta.output_tokens === "number"
		) {
			metaElement.append(
				`<div><strong>Tokens:</strong> Input: ${item.meta.input_tokens}, Output: ${item.meta.output_tokens}</div>`
			);
		}
		if (typeof item.meta.cost === "number") {
			metaElement.append(`<div><strong>Cost:</strong> $${item.meta.cost.toFixed(6)}</div>`);
		}
		if (item.meta.end_reason) {
			metaElement.append(`<div><strong>End Reason:</strong> ${item.meta.end_reason}</div>`);
		}
		itemElement.append(metaElement);

		if (item.content && Array.isArray(item.content)) {
			const contentList = $('<ul class="item-content-list"></ul>');
			item.content.forEach((contentItem) => {
				const contentElement = $('<li class="item-content"></li>');
				contentElement.addClass(`content-${contentItem.type}`);
				let contentHtml = "";

				switch (contentItem.type) {
					case "text":
						contentHtml = `<strong>Text:</strong><div class="content-value">${escapeHtml(
							contentItem.text
						)}</div>`;
						break;
					case "thinking":
						contentHtml = `<strong>Thinking:</strong><div class="content-value">${escapeHtml(
							contentItem.text
						)}</div>`;
						break;
					case "tool_use":
						let toolResultHtml = "";
						if (contentItem.result !== null && contentItem.result !== undefined) {
							let resultDisplay = escapeHtml(String(contentItem.result));
							try {
								const parsedResult = JSON.parse(contentItem.result);
								resultDisplay = escapeHtml(JSON.stringify(parsedResult, null, 2));
								toolResultHtml = `<strong>Result:</strong><pre class="tool-result">${resultDisplay}</pre>`;
							} catch (e) {
								toolResultHtml = `<strong>Result:</strong><pre class="tool-result">${resultDisplay}</pre>`;
							}
						}
						contentHtml =
							`<div class="tool-name">Tool: ${escapeHtml(
								contentItem.name
							)} (ID: ${escapeHtml(contentItem.id)})</div>` +
							`<strong>Args:</strong><pre class="tool-args">${escapeHtml(
								JSON.stringify(contentItem.args, null, 2)
							)}</pre>` +
							`<div class="tool-status"><strong>Status:</strong> <span class="tool-status-${escapeHtml(
								contentItem.status
							)}">${escapeHtml(contentItem.status)}</span></div>` +
							toolResultHtml;
						break;
					case "image":
						contentHtml = `<strong>Image:</strong>`;
						if (contentItem.url) {
							contentHtml += `<div class="content-value"><img src="${encodeURI(
								contentItem.url
							)}" alt="Image content"></div>`;
						} else if (contentItem.data) {
							contentHtml += `<div class="content-value"><img src="data:image/png;base64,${contentItem.data}" alt="Image content (embedded)"></div>`; // Assuming PNG, adjust if other types are common
						}
						break;
					case "file":
						contentHtml = `<strong>File:</strong><div class="content-value"><a href="data:application/pdf;base64,${
							contentItem.data
						}" download="${escapeHtml(contentItem.name)}">${escapeHtml(
							contentItem.name
						)}</a></div>`; // Assuming PDF
						break;
					default:
						contentHtml = `<strong>Unknown content type: ${escapeHtml(
							contentItem.type
						)}</strong><pre>${escapeHtml(JSON.stringify(contentItem, null, 2))}</pre>`;
				}
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

	// Create a new div for the formatted display
	const display_wrapper = $("<div>")
		.addClass("otto-execution-formatted-display")
		.insertBefore(execution_field.wrapper);

	// Add note about dedicated display field
	const note = $(
		'<p class="text-muted small">Formatted view of the Execution. Raw JSON below.</p>'
	);
	display_wrapper.parent().prepend(note); // Prepend to the parent of the display_wrapper, which should be the same parent as execution_field.wrapper

	return display_wrapper;
}
