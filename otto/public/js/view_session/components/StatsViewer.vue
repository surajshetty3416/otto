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
		<Detail
			label="Cost"
			:title="`Total cost of the session: $${stats.cost.toFixed(6)}`"
			:value="`$${stats.cost.toFixed(6)}`"
		/>
		<Detail
			label="Duration"
			:title="`Duration of the session (from first request to last response): ${format_duration(
				stats.duration
			)}`"
			:value="format_duration(stats.duration)"
		/>
		<Detail
			label="Total Input Tokens"
			:title="`Total number of tokens sent to provider: ${stats.total_input_tokens} tok`"
			:value="format_number(stats.total_input_tokens) + ' tok'"
		/>
		<Detail
			label="Total Output Tokens"
			:title="`Total number of tokens received from provider: ${stats.total_output_tokens} tok`"
			:value="format_number(stats.total_output_tokens) + ' tok'"
		/>
		<Detail
			label="LLM Calls"
			:title="`Number of LLM provider API calls made in this session: ${stats.llm_calls}`"
			:value="format_number(stats.llm_calls)"
		/>
		<Detail
			v-if="stats.tokens_per_second"
			:title="`Average tokens per second: ${stats.tokens_per_second} tok/s`"
			label="Tokens per second"
			:value="format_number(stats.tokens_per_second) + ' tok/s'"
		/>
		<Detail
			v-if="stats.max_input_tokens !== stats.total_input_tokens"
			label="Max Input Tokens"
			:title="`Maximum number of input tokens used in a single call: ${stats.max_input_tokens} tok`"
			:value="format_number(stats.max_input_tokens) + ' tok'"
		/>
		<Detail
			v-if="stats.max_output_tokens !== stats.total_output_tokens"
			label="Max Output Tokens"
			:title="`Maximum number of output tokens received in a single call: ${stats.max_output_tokens} tok`"
			:value="format_number(stats.max_output_tokens) + ' tok'"
		/>
		<Detail
			v-if="stats.time_to_first_chunk"
			:title="`Average time taken to receive the first chunk from provider: ${stats.time_to_first_chunk} seconds`"
			label="Time to first chunk"
			:value="format_duration(stats.time_to_first_chunk)"
		/>
		<Detail
			v-if="stats.inter_chunk_latency"
			:title="`Average time between consecutive chunks received: ${stats.inter_chunk_latency} seconds`"
			label="Inter chunk latency"
			:value="format_duration(stats.inter_chunk_latency)"
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
