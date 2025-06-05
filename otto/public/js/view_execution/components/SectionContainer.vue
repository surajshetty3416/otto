<script setup>
import { ref } from "vue";
import SectionHeader from "./SectionHeader.vue";

const props = defineProps({
	title: {
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
});

const isOpen = ref(true);
</script>

<template>
	<div class="section">
		<SectionHeader
			v-if="title"
			:title="title"
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
