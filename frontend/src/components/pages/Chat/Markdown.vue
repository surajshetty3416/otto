<template>
	<div
		ref="containerRef"
		class="markdown-content prose prose-sm max-w-none"
		v-html="content"
	></div>
</template>

<script setup lang="ts">
import { escapeHtml } from "@/utils";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";
import { Marked } from "marked";
import { markedHighlight } from "marked-highlight";
import { computed, h, nextTick, ref, render, watch, type VNode } from "vue";
import DOMPurify from "dompurify";
import { Copy, Check } from "lucide-vue-next";
import { toast } from "vue-sonner";

const slots = defineSlots<{
	default: () => VNode[];
}>();
const props = defineProps<{
	isStreaming?: boolean;
}>();

const containerRef = ref<HTMLElement | null>(null);

// Create a new marked instance with proper configuration
const markedInstance = new Marked(
	markedHighlight({
		langPrefix: "hljs language-",
		highlight(code, lang) {
			const language = hljs.getLanguage(lang) ? lang : "plaintext";
			return hljs.highlight(code, { language }).value;
		},
	})
);

// Configure marked to handle HTML properly
markedInstance.setOptions({
	gfm: true, // GitHub Flavored Markdown
	breaks: true, // Convert \n to <br>
});

const content = computed(() => {
	const rendered = renderedContent.value;
	return DOMPurify.sanitize(rendered, { USE_PROFILES: { html: true } });
});

const renderedContent = computed(() => {
	const slotContent = slots.default?.();
	const content = slotContent?.[0]?.children?.toString() || "";
	try {
		// Get the text content from the default slot

		if (!props.isStreaming) {
			return markedInstance.parse(content) as string;
		}

		// If streaming, parse only lines that have reached the end
		// this to some extent ensures that elements with matching tags
		// aren't rendered weirdly. (doesn't work for multiline elements)
		const lines = content.split("\n");
		const toParse = lines.slice(0, -1).join("\n");

		// Escape the last line to prevent XSS while streaming
		const lastLine = escapeHtml(lines.at(-1) || "");
		return [markedInstance.parse(toParse), lastLine].join("\n");
	} catch (error) {
		console.error("Error parsing markdown:", error);
		// Escape content on error to prevent XSS
		return escapeHtml(content);
	}
});

// Add copy buttons to code blocks after rendering

async function addCopyButtonReaction() {
	await nextTick();
	if (!containerRef.value) return;
	addCopyButtonsToCodeBlocks(containerRef.value);
}

watch(() => [content.value, containerRef.value], addCopyButtonReaction);

function addCopyButtonsToCodeBlocks(container: HTMLElement) {
	if (props.isStreaming) return;
	const targets = container.querySelectorAll("pre:has(code)");
	for (const target of Array.from(targets)) {
		if (target.querySelector(".copy-button")) return;

		const codeElement = target.querySelector("code");
		if (!codeElement) return;

		(target as HTMLElement).style.position = "relative";
		const buttonContainer = document.createElement("div");
		buttonContainer.className = "copy-button";

		// @ts-ignore - isCopied is used in the render function
		let isCopied = false;
		let timeoutId: number | null = null;

		const handleCopy = async () => {
			const textToCopy = codeElement.innerText;
			try {
				await navigator.clipboard.writeText(textToCopy);
				isCopied = true;

				// Re-render the button with check icon
				render(copiedButton, buttonContainer);

				// Reset after 2 seconds
				if (timeoutId) clearTimeout(timeoutId);
				timeoutId = window.setTimeout(() => {
					isCopied = false;
					render(copyButton, buttonContainer);
				}, 2000);
			} catch (err) {
				toast.error("Failed to copy");
				console.error("Failed to copy:", err);
			}
		};

		const copyButton = h(
			"button",
			{
				class: "copy-btn",
				"aria-label": "Copy code",
				title: "Copy code",
				onClick: handleCopy,
			},
			h(Copy, { size: 16 })
		);

		const copiedButton = h(
			"button",
			{
				class: "copy-btn copied",
				"aria-label": "Copied!",
				title: "Copied!",
				onClick: handleCopy,
			},
			h(Check, { size: 16 })
		);

		render(copyButton, buttonContainer);
		target.appendChild(buttonContainer);
	}
}
</script>

<style scoped>
.markdown-content {
	/* CSS Variables for easy customization */
	/* All font sizes are now in 'em' units to scale with parent font-size */
	--md-font-size-base: 1em;
	--md-font-size-h1: 1.65em;
	--md-font-size-h2: 1.35em;
	--md-font-size-h3: 1.25em;
	--md-font-size-h4: 1.15em;
	--md-font-size-h5: 1.1em;
	--md-font-size-h6: 1.05em;
	--md-font-size-code: 0.9125em;

	--md-font-weight-normal: 400;
	--md-font-weight-medium: 500;
	--md-font-weight-semibold: 600;
	--md-font-weight-bold: 700;

	--md-line-height-base: 1.5;
	--md-line-height-heading: 1.25;

	--md-color-code-bg: theme(colors.gray.50);

	--md-spacing-paragraph: 0.75em;
	--md-spacing-heading-top: 1.65em;
	--md-spacing-heading-bottom: 0.75em;

	/* Default base font size - can be overridden via inline styles */
	font-size: 1rem;
	font-weight: var(--md-font-weight-medium);
	line-height: var(--md-line-height-base);
}

.markdown-content :deep(h1) {
	font-size: var(--md-font-size-h1);
	font-weight: var(--md-font-weight-bold);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(h2) {
	font-size: var(--md-font-size-h2);
	font-weight: var(--md-font-weight-bold);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(h3) {
	font-size: var(--md-font-size-h3);
	font-weight: var(--md-font-weight-semibold);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(h4) {
	font-size: var(--md-font-size-h4);
	font-weight: var(--md-font-weight-semibold);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(h5) {
	font-size: var(--md-font-size-h5);
	font-weight: var(--md-font-weight-semibold);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(h6) {
	font-size: var(--md-font-size-h6);
	font-weight: var(--md-font-weight-semibold);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(p) {
	font-size: var(--md-font-size-base);
	margin-bottom: var(--md-spacing-paragraph);
}

.markdown-content :deep(code) {
	font-size: var(--md-font-size-code);
	background-color: var(--md-color-code-bg);
	padding: 0.15rem 0.25rem;
	border-radius: 0.35rem;
}

.markdown-content :deep(code)::before,
.markdown-content :deep(code)::after {
	content: "";
}

.markdown-content :deep(strong) {
	font-weight: var(--md-font-weight-bold);
}

.markdown-content :deep(em) {
	font-style: italic;
}

.markdown-content :deep(pre) {
	padding: 0.5rem 0.5rem;
	border-radius: 0;
	background-color: var(--md-color-code-bg);
	border: 1px solid theme("colors.gray.200");
}

.markdown-content :deep(pre:has(code)),
.markdown-content :deep(pre > code) {
	background-color: theme("colors.gray.50");
	color: theme("colors.gray.900");
}

.markdown-content :deep(pre:has(code)) {
	border: 1px solid theme("colors.gray.200");
	border-radius: theme("borderRadius.lg");
}

/* Copy button styles */
.markdown-content :deep(.copy-button) {
	position: absolute;
	top: 0.5rem;
	right: 0.5rem;
	opacity: 0;
	transition: opacity 0.2s ease;
}

.markdown-content :deep(pre:hover .copy-button) {
	opacity: 1;
}

.markdown-content :deep(.copy-btn) {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0.375rem;
	background-color: theme("colors.white");
	border: 1px solid theme("colors.gray.300");
	border-radius: theme("borderRadius.md");
	cursor: pointer;
	transition: all 0.2s ease;
	color: theme("colors.gray.600");
}

.markdown-content :deep(.copy-btn:hover) {
	background-color: theme("colors.gray.50");
	color: theme("colors.gray.900");
	border-color: theme("colors.gray.400");
}

.markdown-content :deep(.copy-btn.copied) {
	color: theme("colors.green.600");
	border-color: theme("colors.green.300");
	background-color: theme("colors.green.50");
}

.markdown-content :deep(.copy-btn svg) {
	display: block;
}
</style>
