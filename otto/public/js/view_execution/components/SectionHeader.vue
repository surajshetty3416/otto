<script setup>
import { computed } from "vue";
const emit = defineEmits(["update:modelValue"]);

const props = defineProps({
	title: { type: String, required: true },
	modelValue: { type: Boolean, default: false },
});

const icon = computed(() => {
	return props.modelValue
		? frappe.utils.icon("chevron-down", "sm")
		: frappe.utils.icon("chevron-up", "sm");
});
</script>

<template>
	<div class="section-header" @click="() => emit('update:modelValue', !modelValue)">
		<h2 class="section-header-title">{{ title }}</h2>
		<div v-html="icon"></div>
	</div>
</template>

<style scoped>
.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: var(--padding-xs) var(--padding-md);
	cursor: pointer;

	h2 {
		color: var(--gray-800);
		font-size: var(--text-md);
		margin: 0;
	}
}

.section-header:hover {
	background-color: var(--gray-50);
}
</style>
