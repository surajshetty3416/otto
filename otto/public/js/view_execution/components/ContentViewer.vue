<script setup>
import { computed } from "vue";
import ObjectViewer from "./ObjectViewer.vue";

const props = defineProps({
	value: { type: [Object, String], required: true },
});

const content = computed(() => {
	if (typeof props.value === "object") {
		const value = { ...props.value };
		delete value.explanation;
		return value;
	}

	try {
		console.log(props.value);
		const value = JSON.parse(props.value);
		delete value.explanation;
		return value;
	} catch {
		return props.value;
	}
});

const explanation = computed(() => {
	if (typeof props.value === "object") {
		return props.value.explanation;
	}

	try {
		return JSON.parse(props.value).explanation;
	} catch {
		return null;
	}
});

const content_style = computed(() => {
	if (!explanation.value) return "";

	return "border-bottom: 1px solid var(--gray-200);";
});
</script>
<template>
	<div class="content">
		<ObjectViewer
			class="content-object"
			:style="content_style"
			v-if="typeof content === 'object' && Object.keys(content).length > 0"
			:object="content"
		/>
		<pre
			v-else-if="typeof content !== 'object' && content"
			class="content-regular"
			:style="content_style"
			>{{ content }}</pre
		>
		<p v-else class="no-content">No content</p>

		<p v-if="explanation" title="Explanation given by LLM for tool use" class="explanation">
			{{ explanation }}
		</p>
	</div>
</template>

<style scoped>
.content {
	border: 1px solid var(--gray-200);

	.content-regular,
	.content-object {
		padding: var(--padding-xs);
	}

	.content-regular {
		color: var(--gray-700);
	}

	.no-content {
		font-style: italic;
		color: var(--gray-600);
		padding: var(--padding-xs);
		font-size: var(--text-sm);
		margin: 0;
	}

	.explanation {
		padding: 0;
		margin: 0;
		font-size: var(--text-xs);
		color: var(--gray-600);
		padding: var(--padding-xs);
		background-color: var(--gray-50);
	}

	pre {
		margin: 0;
	}
}
</style>
