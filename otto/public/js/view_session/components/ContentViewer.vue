<script setup>
import { computed } from "vue";
import ObjectViewer from "./ObjectViewer.vue";
import PreViewer from "./PreViewer.vue";

const props = defineProps({
	value: { type: [Object, String], required: true },
});

const content = computed(() => {
	if (typeof props.value === "object" && props.value !== null) {
		const value = { ...props.value };
		delete value.explanation;
		return value;
	}

	try {
		const value = JSON.parse(props.value);
		delete value.explanation;
		return value;
	} catch (e) {
		return props.value;
	}
});

const explanation = computed(() => {
	if (typeof props.value === "object" && props.value !== null) {
		return props.value.explanation;
	}

	try {
		return JSON.parse(props.value).explanation;
	} catch (e) {
		return null;
	}
});
</script>
<template>
	<div class="content">
		<ObjectViewer
			class="content-object"
			v-if="typeof content === 'object' && Object.keys(content).length > 0"
			:object="content"
		/>
		<PreViewer
			v-else-if="typeof content !== 'object' && content"
			class="content-regular"
			:value="content"
		/>
		<p v-else class="no-content">No content</p>

		<p
			v-if="explanation"
			title="Explanation is a meta arg used by the LLM to explain the tool use"
			class="explanation"
		>
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
		font-style: italic;
		padding: 0;
		margin: 0;
		font-size: var(--text-xs);
		color: var(--gray-600);
		padding: var(--padding-xs);
		border-top: 1px dashed var(--gray-300);
	}

	pre {
		margin: 0;
	}
}
</style>
