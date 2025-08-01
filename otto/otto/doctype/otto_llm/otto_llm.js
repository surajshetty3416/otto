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
							<div id="llm-text-response-${id}" title="Text response" style="display: none;"></div>
							<div id="llm-thinking-response-${id}" title="Thinking response" style="font-style: italic; color: var(--gray-700); display: none;"></div>
							<pre id="llm-tool-use-response-${id}" title="Tool use response" style="display: none;"></pre>
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
			const event = `stream-llm-${frm.doc.name}`;
			const responseArea = document.getElementById(`llm-response-area-${id}`);
			const processingContent = document.getElementById(`llm-processing-response-${id}`);
			const textContent = document.getElementById(`llm-text-response-${id}`);
			const thinkingContent = document.getElementById(`llm-thinking-response-${id}`);
			const toolUseContent = document.getElementById(`llm-tool-use-response-${id}`);

			textContent.innerHTML = "";
			thinkingContent.innerHTML = "";
			toolUseContent.innerHTML = "";

			// Clear previous response and reset
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
						toolUseContent.innerHTML = frappe.utils.escape_html(
							toolUseContent.innerHTML + chunk.content
						);
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

					if (message.error) {
						frappe.msgprint(message.error, __("Error"));
					}

					if (message.message === "success") {
						frappe.toast({
							title: __("Success"),
							message: __("Response generation completed"),
							indicator: "green",
						});
					}
				},
			});
		}

		frm.add_custom_button(__("Ask"), ask_dialog);
		frappe.ui.keys.add_shortcut({ shortcut: "shift+a", action: ask_dialog, page: frm.page });
	},
});
