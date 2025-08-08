// Copyright (c) 2025, Alan Tom and contributors
// For license information, please see license.txt

frappe.ui.form.on("Otto LLM", {
	refresh(frm) {
		const id = Math.random().toString(36).substring(2, 15);

		function ask_dialog() {
			const run_dialog = new frappe.ui.Dialog({
				title: __("Ask LLM"),
				fields: [
					{
						fieldname: "message",
						fieldtype: "HTML",
						options: `<div>Test the LLM by asking it a query.</div>`,
					},
					{
						fieldname: "spacer",
						fieldtype: "HTML",
						options: `<br>`,
					},
					{
						fieldname: "query",
						label: __("Query"),
						fieldtype: "Data",
						default: "Hello, how are you?",
						reqd: 1,
					},
					{
						fieldname: "instruction",
						label: __("Instruction"),
						fieldtype: "Data",
						default: "You are a helpful assistant.",
						description: __("The system prompt or instruction for the LLM"),
						reqd: 1,
					},
					{
						fieldname: "reasoning_effort",
						label: __("Reasoning Effort"),
						fieldtype: "Select",
						default: "None",
						options: ["None", "Low", "Medium", "High"],
						description: __("Valid only if model supports reasoning"),
					},
					{
						fieldname: "response_section",
						fieldtype: "HTML",
						options: `<div 
						id="llm-response-area-${id}" 
						style="
							margin-top: var(--padding-md);
							padding: var(--padding-sm);
							border-radius: var(--border-radius);
							background-color: var(--gray-100);
							max-height: 400px;
							overflow-y: auto;
							display: none;"
						>
							<div id="llm-processing-response-${id}" title="Response content" style="display: none; color: var(--gray-500); font-size: var(--text-sm);">Processing query...</div>
							<div id="llm-thinking-response-${id}" title="Thinking response" style="font-style: italic; color: var(--gray-700); display: none;"></div>
							<div id="llm-text-response-${id}" title="Text response" style="display: none;"></div>
							<div id="llm-tool-use-response-${id}" title="Tool use response" style="display: none;"></div>
							<div id="llm-stats-response-${id}" title="Response stats" style="display: none; font-size: var(--text-xs); margin-bottom: 0;"></div>
							<div id="llm-error-response-${id}" title="Response error" style="display: none; font-size: var(--text-xs); margin-bottom: 0; color: var(--red-500);"></div>
						</div>`,
					},
				],
				primary_action_label: __("Ask"),
				primary_action(values) {
					const responseArea = document.getElementById(`llm-response-area-${id}`);
					const processingResponse = document.getElementById(
						`llm-processing-response-${id}`
					);

					if (responseArea && processingResponse) {
						responseArea.style.display = "flex";
						responseArea.style.flexDirection = "column";
						responseArea.style.gap = "var(--padding-md)";
						processingResponse.style.display = "block";
					}

					run_dialog.get_primary_btn().prop("disabled", true);

					ask(values.query, values.instruction, values.reasoning_effort, run_dialog);
				},
			});
			run_dialog.show();
		}

		function ask(query, instruction, reasoning_effort, dialog) {
			const responseArea = document.getElementById(`llm-response-area-${id}`);
			const processingContent = document.getElementById(`llm-processing-response-${id}`);
			const textContent = document.getElementById(`llm-text-response-${id}`);
			const thinkingContent = document.getElementById(`llm-thinking-response-${id}`);
			const toolUseContent = document.getElementById(`llm-tool-use-response-${id}`);
			const statsContent = document.getElementById(`llm-stats-response-${id}`);
			const errorContent = document.getElementById(`llm-error-response-${id}`);

			errorContent.style.display = "none";
			statsContent.style.display = "none";
			textContent.innerHTML = "";
			thinkingContent.innerHTML = "";
			toolUseContent.innerHTML = "";
			processingContent.style.display = "block";

			// Clear previous response and reset
			const event = "stream-llm";
			frappe.realtime.off(event);
			frappe.realtime.on(event, (data) => {
				console.log(data);
				processingContent.style.display = "none";
				if (!data.chunk) {
					return;
				}

				const chunk = data.chunk;

				// Format content based on type
				switch (chunk.type) {
					case "thinking":
						thinkingContent.style.display = "block";
						thinkingContent.innerHTML = frappe.utils.escape_html(
							thinkingContent.innerHTML + chunk.content
						);
						break;
					case "tool_use":
						toolUseContent.style.display = "block";
						toolUseContent.innerHTML = `<pre>${frappe.utils.escape_html(
							chunk.content
						)}</pre>`;
						break;
					case "text":
					default:
						textContent.style.display = "block";
						textContent.innerHTML = frappe.utils.escape_html(
							textContent.innerHTML + chunk.content
						);
						break;
				}

				responseArea.scrollTop = responseArea.scrollHeight;
			});

			function update_ui({ item, error }) {
				console.log(item, error);
				processingContent.style.display = "none";
				if (!item || error) {
					errorContent.style.display = "block";
					errorContent.innerHTML = error || "No response item received";
					return;
				}

				const stats = [
					`Input tokens: ${item.meta.input_tokens.toLocaleString()}`,
					`Output tokens: ${item.meta.output_tokens.toLocaleString()}`,
					`Duration: ${format_duration(item.meta.end_time - item.meta.start_time)}`,
					`Cost: $${item.meta.cost}`,
					`Tokens per second: ${
						item.meta.output_tokens / (item.meta.end_time - item.meta.start_time)
					} tok/s`,
					`Inter chunk latency: ${format_duration(item.meta.inter_chunk_latency)}`,
					`Time to first chunk: ${format_duration(item.meta.time_to_first_chunk)}`,
				];

				statsContent.innerHTML = stats.join("<br>");
				statsContent.style.display = "block";

				for (const c of item.content) {
					switch (c.type) {
						case "thinking":
							thinkingContent.style.display = "block";
							thinkingContent.innerHTML = frappe.utils.escape_html(c.text);
							break;
						case "tool_use":
							toolUseContent.style.display = "block";
							toolUseContent.innerHTML = `<pre>${frappe.utils.escape_html(
								JSON.stringify(
									{
										id: c.id,
										name: c.name,
										args: c.args,
									},
									null,
									2
								)
							)}</pre>`;
							break;
						case "text":
						default:
							textContent.style.display = "block";
							textContent.innerHTML = frappe.utils.escape_html(c.text);
							break;
					}
				}
			}

			frappe.call({
				method: "ask",
				doc: frm.doc,
				args: {
					query,
					instruction,
					reasoning_effort,
				},
				callback({ message }) {
					dialog.get_primary_btn().prop("disabled", false);
					update_ui(message);
				},
			});
		}

		frm.add_custom_button(__("Ask"), ask_dialog);
		frappe.ui.keys.add_shortcut({ shortcut: "shift+a", action: ask_dialog, page: frm.page });
	},
});

function format_duration(duration, fixed = 2) {
	if (duration < 1) {
		return `${(duration * 1000).toFixed(fixed)}ms`;
	}

	if (duration < 60) {
		return `${duration.toFixed(fixed)}s`;
	}

	return frappe.utils.get_formatted_duration(duration);
}
