<script setup>
import { get_chevron } from "../utils";
const emit = defineEmits(["update:modelValue"]);

const props = defineProps({
	modelValue: { type: Boolean, required: true },
	index: { type: Number, required: true },
	label: { type: String, required: true },
});
</script>
<template>
	<div class="header" title="Toggle Content" @click="emit('update:modelValue', !modelValue)">
		<p>
			<span :title="`Content Index: ${index + 1}`" class="index">{{ index + 1 }}.</span>
			{{ label }}
		</p>
		<div v-html="get_chevron(modelValue)"></div>
	</div>
</template>
<style scoped>
.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-size: var(--text-sm);
	padding: var(--padding-xs) 0;

	p {
		font-size: var(--text-xs);
		color: var(--gray-900);
		font-weight: 600;
		margin: 0;
	}

	&:hover {
		background-color: var(--gray-50);
		cursor: pointer;
	}

	.index {
		color: var(--gray-500);
		font-weight: normal;
	}
}
</style>
