<script setup>
import { format_duration, format_number } from "../utils";
import Detail from "./Detail.vue";

const props = defineProps({
	stats: {
		type: Object,
		required: true,
	},
	slug_map: {
		type: Object,
		required: true,
	},
});
</script>
<template>
	<div class="stats-container">
		<Detail label="Cost" :value="`$${stats.cost.toFixed(6)}`" />
		<Detail
			label="Total Input Tokens"
			:value="format_number(stats.total_input_tokens) + ' tok'"
		/>
		<Detail
			label="TotalOutput Tokens"
			:value="format_number(stats.total_output_tokens) + ' tok'"
		/>
		<Detail
			label="Duration"
			:value="format_duration(stats.duration)"
			:title="`${stats.duration} seconds`"
		/>
		<Detail label="LLM Calls" :value="format_number(stats.llm_calls)" />
		<Detail label="Max Input Tokens" :value="format_number(stats.max_input_tokens) + ' tok'" />
		<Detail
			label="Max Output Tokens"
			:value="format_number(stats.max_output_tokens) + ' tok'"
		/>
	</div>
</template>
<style scoped>
.stats-container {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--padding-md);
}

.tool-stats-wrapper {
	margin-top: var(--padding-md);
}

.tool-stats-container {
	border-top: 1px solid var(--gray-200);
	max-height: 318px;
	overflow: auto;
}

.tool-stats-grid {
	display: grid;
	grid-template-columns: 2fr 1fr 1fr 1fr;
	gap: var(--padding-md);
	padding: var(--padding-xs) 0;
	align-items: center;
	font-size: var(--text-xs);
}

.tool-stats-grid.header {
	position: sticky;
	top: 0;
	font-size: var(--text-xs);
	font-weight: 600;
	color: var(--gray-500);
	background-color: var(--white);
}

.tool-stats-grid {
	border-bottom: 1px dashed var(--gray-300);
}

.tool-stats-grid:not(.header):last-child {
	padding-bottom: 0;
	border-bottom: none;
}

.tool-name {
	font-family: monospace;
	font-weight: 600;
	color: var(--gray-600);

	span {
		font-size: var(--text-xs);
		color: var(--violet-500);
		font-weight: normal;
	}
}

.text-right {
	text-align: right;
}
</style>
