<script setup>
const props = defineProps({
	value: { type: String, required: true },
});
</script>

<template>
	<pre class="value">{{ value }}</pre>
</template>

<style scoped>
.value {
	color: var(--gray-700);
	font-size: var(--text-sm);
	font-family: monospace;
	margin: 0;
	padding: 0;
	overflow-x: auto;
	/* white-space: pre; */
}
</style>
