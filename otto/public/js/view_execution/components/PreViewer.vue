<script setup>
import { computed } from "vue";
import hljs from "highlight.js";

const props = defineProps({
	value: { required: true },
});

function isJson(str) {
	try {
		JSON.parse(str);
		return true;
	} catch (e) {
		return false;
	}
}

function isMarkdown(str) {
	// Heuristics to detect markdown.
	const markdownPatterns = [
		/^#\s/m, // headings
		/^\s*-\s/m, // lists
		/^\s*\*\s/m, // lists
		/^\s*>\s/m, // blockquotes
		/\[.+\]\(.+\)/, // links
		/!\[.+\]\(.+\)/, // images
		/`{1,3}/, // code
		/\*{1,2}[^\*]+\*{1,2}/, // emphasis
		/~{2}[^~]+~{2}/, // strikethrough
	];
	return markdownPatterns.some((pattern) => pattern.test(str));
}

function isHtml(str) {
	// Heuristic to detect HTML. True if it finds a string that looks like an opening tag.
	return /<[a-z]/i.test(str) || /&lt;[a-z]/i.test(str);
}

const highlightedValue = computed(() => {
	if (typeof props.value !== "string") {
		return hljs.highlight(String(props.value), { language: "plaintext" }).value;
	}

	if (isJson(props.value)) {
		return hljs.highlight(props.value, { language: "json" }).value;
	}

	if (isMarkdown(props.value)) {
		return hljs.highlight(props.value, { language: "markdown" }).value;
	}

	if (isHtml(props.value)) {
		const unescapedValue = props.value.replace(/&lt;/g, "<").replace(/&gt;/g, ">");
		return hljs.highlight(unescapedValue, { language: "xml" }).value;
	}

	return hljs.highlight(props.value, { language: "plaintext" }).value;
});
</script>

<template>
	<pre class="value"><code class="hljs" v-html="highlightedValue" /></pre>
</template>

<style>
@import "highlight.js/styles/github.css";
</style>

<style scoped>
.value {
	font-size: var(--text-sm);
	font-family: monospace;
	margin: 0;
	padding: 0;
	overflow-x: auto;
	white-space: pre-wrap;
	word-wrap: break-word;
}

.value .hljs {
	padding: 0;
	background-color: transparent;
}
</style>
