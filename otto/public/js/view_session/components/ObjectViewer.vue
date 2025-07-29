<script setup>
import { copy_to_clipboard } from "../utils";
import PreViewer from "./PreViewer.vue";
const props = defineProps({
	object: { type: Object, required: true },
});

function format(value) {
	if (typeof value === "object") {
		try {
			return JSON.stringify(value, null, 2);
		} catch (e) {
			return value;
		}
	}

	return value;
}
</script>

<template>
	<div class="container">
		<template v-for="(value, key) in object" :key="key">
			<div class="item">
				<div
					class="key"
					:title="`Click to copy value of ${key}`"
					@click="copy_to_clipboard(value)"
				>
					{{ key }}
				</div>
				<PreViewer :value="format(value)" />
			</div>
		</template>
	</div>
</template>

<style scoped>
.container {
	display: flex;
	flex-direction: column;
	gap: var(--spacing-sm);
}

.key {
	color: var(--gray-500);
	font-size: var(--text-xs);
	font-family: monospace;
	margin: 0;
	padding: 0;
	cursor: pointer;
}

.item {
	border-bottom: 1px dashed var(--gray-300);
	padding-bottom: var(--padding-sm);
	padding-top: var(--padding-sm);
}

.item:last-child {
	border-bottom: none;
	padding-bottom: 0;
}

.item:first-child {
	padding-top: 0;
}
</style>
