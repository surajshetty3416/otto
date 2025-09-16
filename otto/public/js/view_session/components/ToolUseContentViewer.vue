<script setup>
import { ref } from "vue";
import {
	copy_to_clipboard,
	format_date,
	format_duration,
	get_chevron,
	get_status_color,
	get_status_style,
} from "../utils";
import ContentViewer from "./ContentViewer.vue";

const props = defineProps({
	index: { type: Number, required: true },
	call: { type: Object, required: true },
	tool: { type: Object, required: true },
});
const show = ref(false);
</script>
<template>
	<div class="container" :style="{ borderLeftColor: get_status_color(call.status, 200) }">
		<div @click="show = !show" class="call-row-header">
			<!-- Slug Index, Timestamp -->
			<div class="left">
				<div
					:style="get_status_style(call.status)"
					class="status"
					:title="`Status: ${call.status}`"
				>
					{{ call.status }}
				</div>

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

				<div v-html="get_chevron(show)"></div>
			</div>
		</div>

		<!-- Row Body -->
		<div class="row-body" v-if="show">
			<!-- Args -->
			<div class="row-body-item">
				<div
					class="label"
					title="Args passed to the tool by the LLM. Click to copy."
					@click="copy_to_clipboard(call.args)"
				>
					Args
				</div>
				<ContentViewer :value="call.args" class="content-viewer" />
			</div>

			<!-- Override -->
			<div class="row-body-item" v-if="call.override">
				<div
					class="label"
					title="Arg overrides provided by the user. Click to copy."
					@click="copy_to_clipboard(call.override)"
				>
					Overrides
				</div>
				<ContentViewer :value="call.override" class="content-viewer" />
			</div>

			<!-- Result -->
			<div class="row-body-item">
				<div
					class="label"
					title="Result returned by the tool given to the LLM. Click to copy."
					@click="copy_to_clipboard(call.result)"
				>
					Result
				</div>
				<ContentViewer :value="call.result" class="content-viewer" />
			</div>

			<!-- Stdout -->
			<div class="row-body-item" v-if="call.stdout">
				<div
					class="label"
					title="Output printed to stdout by the tool. Click to copy."
					@click="copy_to_clipboard(call.stdout)"
				>
					Stdout
				</div>
				<ContentViewer :value="call.stdout" class="content-viewer" />
			</div>

			<!-- Stderr -->
			<div class="row-body-item" v-if="call.stderr">
				<div
					class="label"
					title="Output printed to stderr by the tool. Click to copy."
					@click="copy_to_clipboard(call.stderr)"
				>
					Stderr
				</div>
				<ContentViewer :value="call.stderr" class="content-viewer" />
			</div>
		</div>
	</div>
</template>

<style scoped>
.container {
	border: 1px solid var(--gray-200);
	border-left: 3px solid;
}

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
		flex-direction: row;
		align-items: center;
		justify-content: center;
		gap: var(--padding-sm);
		font-family: monospace;

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
		padding: 0 var(--padding-xs);
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
		cursor: pointer;
		font-size: var(--text-xs);
		font-family: monospace;
		color: var(--gray-600);
	}

	.content-viewer {
		/* --gray-50 is f8f8f8 */
		background-color: #fbfbfb;
	}
}
</style>
