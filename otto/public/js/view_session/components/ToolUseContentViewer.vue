<script setup>
import { ref } from "vue";
import { format_date, format_duration, get_status_background, get_status_color } from "../utils";
import ContentViewer from "./ContentViewer.vue";

const props = defineProps({
	index: { type: Number, required: true },
	call: { type: Object, required: true },
	tool: { type: Object, required: true },
});
const show = ref(true);
</script>
<template>
	<div>
		<div
			@click="show = !show"
			class="call-row-header"
			:style="{
				backgroundColor: get_status_background(call.status, 50),
			}"
		>
			<!-- Slug Index, Timestamp -->
			<div class="left">
				<p class="index">{{ tool.slug }} #{{ index + 1 }}</p>
				<span class="separator">·</span>

				<p
					class="timestamp"
					:title="`Call Start Time: ${new Date(call.start_time * 1000)}`"
				>
					{{ format_date(call.start_time) }}
				</p>
			</div>

			<!-- Loc, Duration, Status -->
			<div class="right">
				<p
					class="loc"
					:title="`Session Item Index: ${call.index[0]}, Item Content Index: ${call.index[1]}`"
				>
					{{ `[${call.index[0]}, ${call.index[1]}]` }}
				</p>
				<span class="separator">·</span>

				<p
					class="duration"
					:title="`Execution Duration: ${call.end_time - call.start_time}ms`"
				>
					{{ format_duration(call.end_time - call.start_time, 3) }}
				</p>
				<span class="separator">·</span>

				<div
					:style="{
						color: get_status_color(call.status),
					}"
					class="status"
					:title="`Status: ${call.status}`"
				>
					{{ call.status }}
				</div>
			</div>
		</div>

		<!-- Row Body -->
		<div class="row-body" v-if="show">
			<div class="row-body-item">
				<div class="label" title="Args passed to the tool by the LLM">Args</div>
				<ContentViewer :value="call.args" class="content-viewer" />
			</div>

			<div class="row-body-item">
				<div class="label" title="Result returned by the tool given to the LLM">
					Result
				</div>
				<ContentViewer :value="call.result" class="content-viewer" />
			</div>

			<div class="row-body-item" v-if="call.stdout">
				<div class="label" title="Output printed to stdout by the tool">Stdout</div>
				<ContentViewer :value="call.stdout" class="content-viewer" />
			</div>

			<div class="row-body-item" v-if="call.stderr">
				<div class="label" title="Output printed to stderr by the tool">Stderr</div>
				<ContentViewer :value="call.stderr" class="content-viewer" />
			</div>
		</div>
	</div>
</template>

<style scoped>
.call-row-header {
	cursor: pointer;
	display: flex;
	justify-content: space-between;
	align-items: baseline;
	gap: var(--padding-sm);
	padding: var(--padding-xs);

	&:hover {
		background-color: var(--gray-50) !important;
	}

	div {
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: var(--padding-sm);
		font-family: monospace;

		.left {
			gap: var(--padding-lg);
		}

		.index {
			font-style: italic;
		}

		p {
			margin: 0;
			padding: 0;
			font-size: var(--text-xs);
			color: var(--gray-600);
		}

		.separator {
			color: var(--gray-300);
		}
	}

	.status {
		font-size: var(--text-xs);
		font-weight: 600;
		background-color: transparent !important;
		text-transform: capitalize;
		margin: 0;
	}
}

.row-body {
	display: flex;
	flex-direction: column;
	gap: var(--padding-sm);
	padding: var(--padding-xs);
	border-top: 1px solid var(--gray-200);

	.row-body-item {
		margin-top: var(--padding-sm);
	}

	.label {
		font-size: var(--text-xs);
		font-family: monospace;
		color: var(--gray-600);
	}

	.content-viewer {
		background-color: var(--gray-50);
	}
}
</style>
