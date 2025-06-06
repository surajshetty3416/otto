<script setup>
const props = defineProps({
	object: { type: Object, required: true },
});
</script>

<template>
	<div class="container">
		<template v-for="(value, key) in object" :key="key">
			<div class="item">
				<div class="key">{{ key }}</div>
				<pre class="value">{{ value }}</pre>
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
}

.value {
	color: var(--gray-700);
	font-size: var(--text-sm);
	font-family: monospace;
	margin: 0;
	padding: 0;
	overflow-x: auto;
	/* white-space: pre; */
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
