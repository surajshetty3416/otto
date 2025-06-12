<script setup>
import { ref } from "vue";
import PreViewer from "./PreViewer.vue";
import ContentSectionHeader from "./ContentSectionHeader.vue";

const props = defineProps({
	index: { type: Number, required: true },
	value: { type: String, required: true },
	isThinking: { type: Boolean, required: true },
});

const show = ref(!props.isThinking);
</script>

<template>
	<div>
		<ContentSectionHeader
			v-model="show"
			:index="index"
			:label="isThinking ? 'Thinking' : 'Text'"
		/>
		<PreViewer v-if="show" class="content" :value="value" />
	</div>
</template>

<style scoped>
.content {
	padding: var(--padding-sm);
	border: 1px solid var(--gray-200);
	background-color: var(--gray-50);
}
</style>
