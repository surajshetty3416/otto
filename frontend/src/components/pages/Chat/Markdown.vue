<template>
	<div class="markdown-content prose prose-sm max-w-none" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed, useSlots } from "vue";
import { marked } from "marked";
import { markedHighlight } from "marked-highlight";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

const slots = useSlots();
const props = defineProps<{
	isStreaming?: boolean;
}>();

// Configure marked with syntax highlighting
marked.use(
	markedHighlight({
		langPrefix: "hljs language-",
		highlight(code, lang) {
			const language = hljs.getLanguage(lang) ? lang : "plaintext";
			return hljs.highlight(code, { language }).value;
		},
	})
);

const renderedContent = computed(() => {
	const slotContent = slots.default?.();
	const content = slotContent?.[0]?.children?.toString() || "";
	try {
		// Get the text content from the default slot

		if (!props.isStreaming) return marked.parse(content);

		// If streaming prase only lines that have reached the end
		// this to some extent ensures that elements with matching tags
		// aren't rendered weirdly. (don't work for multiline elements)
		const lines = content.split("\n");
		const toParse = lines.slice(0, -1).join("\n");

		return [marked.parse(toParse), lines.at(-1)].join("\n");
	} catch (error) {
		console.error("Error parsing markdown:", error);
		return content;
	}
});
</script>

<style scoped>
.markdown-content {
	/* CSS Variables for easy customization */
	--md-font-size-base: 1rem;
	--md-font-size-h1: 1.65rem;
	--md-font-size-h2: 1.35rem;
	--md-font-size-h3: 1.25rem;
	--md-font-size-h4: 1.15rem;
	--md-font-size-h5: 1.1rem;
	--md-font-size-h6: 1.05rem;
	--md-font-size-code: 0.9125rem;

	--md-font-weight-normal: 400;
	--md-font-weight-medium: 500;
	--md-font-weight-semibold: 600;
	--md-font-weight-bold: 700;

	--md-line-height-base: 1.5;
	--md-line-height-heading: 1.25;

	--md-color-code-bg: theme(colors.gray.50);

	--md-spacing-paragraph: 0.75rem;
	--md-spacing-heading-top: 1.65rem;
	--md-spacing-heading-bottom: 0.75rem;

	font-size: var(--md-font-size-base);
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
	font-weight: var(--md-font-weight-medium);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(h6) {
	font-size: var(--md-font-size-h6);
	font-weight: var(--md-font-weight-medium);
	line-height: var(--md-line-height-heading);
	margin-top: var(--md-spacing-heading-top);
	margin-bottom: var(--md-spacing-heading-bottom);
}

.markdown-content :deep(p) {
	font-size: var(--md-font-size-base);
	font-weight: var(--md-font-weight-normal);
	margin-bottom: var(--md-spacing-paragraph);
}

.markdown-content :deep(a) {
	font-weight: var(--md-font-weight-medium);
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
</style>
