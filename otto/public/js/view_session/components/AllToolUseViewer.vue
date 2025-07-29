<script setup>
import { reactive } from "vue";
import Link from "./Link.vue";
import {
	format_date,
	format_duration,
	get_link,
	get_status_background,
	get_status_color,
	get_status_style,
} from "../utils";
import ContentViewer from "./ContentViewer.vue";
import ToolUseContentViewer from "./ToolUseContentViewer.vue";

const props = defineProps({
	tool_use: { type: Object, required: true },
});

const show = reactive({});
function get_title(tool) {
	const title = [`Slug: ${tool.slug}`];
	if (tool.slug_original !== tool.slug) {
		title.push(`Original Slug: ${tool.slug_original}`);
	}

	if (tool.description) {
		title.push(`Description: ${tool.description}`);
	}

	if (tool.name) {
		title.push(`Doc: ${tool.name}`);
	}

	if (tool.is_meta) {
		title.push(`This is a meta tool`);
	}

	return title.join("\n");
}
</script>

<template>
	<div>
		<!-- Title Row -->
		<div class="title-row">
			<div class="title">Tool Name</div>
			<div class="stat">Times Called</div>
			<div class="stat">Empty Results</div>
			<div class="stat">Errors</div>
			<div class="stat">Total Duration</div>
		</div>

		<!-- Tool Use Rows -->
		<div>
			<!-- Tool Use, Container -->
			<div v-for="tool in Object.values(props.tool_use)" :key="tool.slug" class="container">
				<!-- Header -->
				<div
					class="header"
					@click="show[tool.slug] = !show[tool.slug]"
					:title="`Click to toggle calls for ${tool.slug}`"
				>
					<!-- Tool Name -->
					<Link
						class="tool-name"
						:link="get_link('Otto Tool', tool.name)"
						:title="get_title(tool)"
						v-if="!tool.is_meta"
					>
						{{ tool.slug }}
					</Link>
					<p class="tool-name" v-else :title="get_title(tool)">
						{{ tool.slug }}
						<span :title="`${tool.slug} is a meta tool`">[meta]</span>
					</p>

					<!-- Times Called -->
					<div class="stat">{{ tool.call_count }}</div>
					<div
						class="stat"
						:title="`${
							(100 * tool.empty_result_count) / tool.call_count
						}% calls are empty`"
					>
						{{ tool.empty_result_count }}
					</div>
					<div
						class="stat"
						:title="`${
							(100 * tool.error_count) / tool.call_count
						}% calls have errored out`"
					>
						{{ tool.error_count }}
					</div>
					<div class="stat" :title="`Total duration: ${tool.total_duration * 1000}ms`">
						{{ format_duration(tool.total_duration, 3) }}
					</div>
				</div>

				<!-- Calls -->
				<template v-if="show[tool.slug] && tool.calls.length > 0">
					<ToolUseContentViewer
						v-for="(call, index) in tool.calls"
						class="call-row"
						:key="'call-' + call.index.join(',')"
						:call="call"
						:index="index"
						:tool="tool"
					/>
				</template>
			</div>
		</div>
	</div>
</template>
<style scoped>
.container {
	border-bottom: 1px solid var(--gray-200);
	padding: 0;

	&:last-of-type {
		border-bottom: none;
	}
}

.tool-name {
	font-family: monospace;
	font-weight: 600;
	color: var(--gray-600);
	padding: 0;
	margin: 0;
	font-size: var(--text-sm);
	width: fit-content;

	span {
		font-size: var(--text-xs);
		color: var(--violet-500);
		font-weight: normal;
	}
}

.header {
	padding: var(--padding-xs) 0;
	cursor: pointer;
	display: grid;
	grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
	gap: var(--padding-xs);

	&:hover {
		background-color: var(--gray-50);
	}

	.stat {
		font-size: var(--text-sm);
		color: var(--gray-600);
		text-align: right;
	}
}

.title-row {
	padding-bottom: var(--padding-xs);
	border-bottom: 1px solid var(--gray-200);
	font-size: var(--text-sm);
	color: var(--gray-600);
	display: grid;
	grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
	gap: var(--padding-xs);

	p {
		font-size: var(--text-xs);
		color: var(--gray-600);
	}

	.stat {
		text-align: right;
	}
}

.call-row {
	margin-bottom: var(--padding-md);

	&:last-of-type {
		margin-bottom: 0;
		border-bottom: none;
	}
}
</style>
