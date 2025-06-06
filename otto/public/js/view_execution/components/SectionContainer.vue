<script setup>
import { ref, watch } from "vue";
import SectionHeader from "./SectionHeader.vue";

const props = defineProps({
	label: {
		type: String,
		required: true,
	},
	isLoading: {
		type: Boolean,
		default: false,
	},
	error: {
		type: String,
		default: null,
	},
	show: {
		type: Boolean,
		default: true,
	},
});

function get_default_state() {
	const stored = localStorage.getItem(`otto_section_${props.label}`);
	if (stored !== null) {
		return stored === "true";
	}

	return props.show;
}
const isOpen = ref(get_default_state());
watch(isOpen, (newVal) => {
	isOpen.value = newVal;
	localStorage.setItem(`otto_section_${props.label}`, newVal);
});
</script>

<template>
	<div class="section">
		<SectionHeader
			v-if="label"
			:title="label"
			v-model="isOpen"
			:style="{
				borderBottom: isOpen ? '1px dashed var(--gray-300)' : '1px solid var(--gray-200) ',
			}"
		/>
		<div class="section-container" v-if="isOpen">
			<div v-if="isLoading" class="loading-spinner">Loading...</div>
			<div v-else-if="error" class="error-message">{{ error }}</div>
			<slot v-else></slot>
		</div>
	</div>
</template>

<style scoped>
.section-container {
	padding: var(--padding-md);
	border-bottom: 1px solid var(--gray-200);
}
</style>
