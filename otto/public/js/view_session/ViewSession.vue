<script setup>
import { onMounted, ref } from "vue";
import AllToolUseViewer from "./components/AllToolUseViewer.vue";
import Detail from "./components/Detail.vue";
import PreViewer from "./components/PreViewer.vue";
import ScrapbookViewer from "./components/ScrapbookViewer.vue";
import SectionContainer from "./components/SectionContainer.vue";
import SessionViewer from "./components/SessionViewer.vue";
import StatsViewer from "./components/StatsViewer.vue";
import { format_date, get_link, link_icon } from "./utils";

const props = defineProps({
	sessionName: {
		type: String,
		required: true,
	},
});

const info = ref(null);
const error = ref(null);
const loading = ref(true);

async function fetchData() {
	let res = {};

	try {
		res = await frappe.call({
			method: "otto.api.session_view.get_session_view",
			args: { name: props.sessionName },
		});
	} catch (e) {
		error.value = e.message || "Failed to load session.";
		loading.value = false;
		return;
	}

	console.log(res);
	info.value = res.message;

	error.value = null;
	loading.value = false;
}

function get_status_style(status) {
	if (status === "Pending") return "color: var(--gray-700); background-color: var(--gray-100);";
	if (status === "Running") return "color: var(--blue-700); background-color: var(--blue-50);";
	if (status === "Success") return "color: var(--green-700); background-color: var(--green-50);";
	if (status === "Failure") return "color: var(--red-700); background-color: var(--red-50);";
}

onMounted(async () => await fetchData());
</script>

<template>
	<div class="session-viewer">
		<!-- 0. Header -->
		<div class="detail-header" v-if="info">
			<a class="name" :href="get_link('Otto Session', info.name)" target="_blank">
				Session <span>{{ info.name }}</span> <span v-html="link_icon"></span
			></a>

			<!-- LLM & Reasoning Effort -->
			<a
				v-if="info.llm"
				class="llm"
				target="_blank"
				:title="`Last LLM used: ${info.llm.title}\nLast reasoning effort: ${info.session.reasoning_effort}`"
				:href="get_link('Otto LLM', info.llm.name)"
			>
				{{ info.llm.title }}
				<span v-if="info.session.reasoning_effort !== 'None'" class="reasoning-effort">
					[{{ info.session.reasoning_effort }}]
				</span>
			</a>
			<span class="separator">·</span>

			<!-- Creation Date -->
			<div
				class="date"
				:title="`Creation date: ${format_date(
					info.session.creation
				)}\nLast updated: ${format_date(info.session.modified)}`"
			>
				{{ format_date(info.session.creation) }}
			</div>
			<span v-if="info.execution" class="separator">·</span>

			<!-- Execution Status (if execution) -->
			<div
				v-if="info.execution"
				:title="`Execution status: ${info.execution.status}`"
				class="status"
				:style="get_status_style(info.execution.status)"
			>
				{{ info.execution.status }}
			</div>
		</div>
		<div v-else-if="loading" class="detail-header">Loading...</div>

		<!-- 1. Execution Details (only if task execution) -->
		<SectionContainer
			v-if="info?.execution"
			title=""
			label=""
			:isLoading="loading"
			:error="error"
		>
			<div>
				<!-- Details -->
				<div class="detail-container">
					<Detail
						v-if="info.execution"
						label="Execution"
						:value="info.execution.name"
						:link="get_link('Otto Execution', info.execution.name)"
					/>
					<Detail
						v-if="info.execution?.task"
						label="Task"
						:value="info.task_title"
						:link="get_link('Otto Task', info.task)"
					/>
					<Detail
						v-if="info.execution?.target_doctype"
						label="Target"
						:value="`${info.execution.target_doctype} - ${info.execution.target}`"
						:link="get_link(info.execution.target_doctype, info.execution.target)"
					/>
					<Detail v-if="info.execution" label="Event" :value="info.execution.event" />
				</div>
			</div>
		</SectionContainer>

		<!-- Stats -->
		<SectionContainer
			v-if="info?.stats"
			title="Stats: metadata about the session run"
			label="Stats"
			:isLoading="loading"
			:error="error"
		>
			<StatsViewer :stats="info.stats" :slug_map="info.slug_map" />
		</SectionContainer>

		<!-- Error -->
		<SectionContainer
			v-if="info?.session?.reason"
			title="Error: reason for the session failure"
			label="Error"
			:show="true"
			:isLoading="loading"
			:error="error"
		>
			<PreViewer :value="info.session.reason" />
		</SectionContainer>

		<!-- Scrapbook -->
		<SectionContainer
			v-if="info?.scrapbooks && info.scrapbooks.length > 0"
			title="Scrapbook: mocked tool args or other logs recorded in Otto Scrapbook"
			label="Scrapbook"
			:isLoading="loading"
			:error="error"
		>
			<template v-for="(book, index) in info.scrapbooks" :key="book.name">
				<ScrapbookViewer v-if="book" :scrapbook="book" :index="index" />
			</template>
		</SectionContainer>

		<!-- Session -->
		<SectionContainer
			v-if="info?.sequence && info.sequence.length > 0"
			title="Session: session sequence of the task"
			label="Session"
			:isLoading="loading"
			:error="error"
		>
			<SessionViewer
				v-for="(item, index) in info.sequence"
				:key="item.id"
				:item="item"
				:index="index"
				:has_task="!!info.task"
			/>
		</SectionContainer>

		<!-- Tool Use -->
		<SectionContainer
			v-if="info?.tool_use && Object.keys(info.tool_use).length > 0"
			title="Tools: tool calls made by the LLM"
			label="Tools"
			:isLoading="loading"
			:error="error"
		>
			<AllToolUseViewer :tool_use="info.tool_use" />
		</SectionContainer>

		<!-- Instruction -->
		<SectionContainer
			v-if="info?.session?.instruction"
			title="Instruction: system prompt used to instruct the LLM on how to execute the task"
			label="Instruction"
			:show="false"
			:isLoading="loading"
			:error="error"
		>
			<PreViewer :value="info.session.instruction" />
		</SectionContainer>
	</div>
</template>
<style scoped>
.detail-header {
	position: sticky;
	top: calc(var(--navbar-height) + var(--page-head-height) + 1px);
	background-color: var(--white);
	z-index: 1;

	display: flex;
	align-items: center;
	gap: var(--padding-md);
	padding: var(--padding-xs) var(--padding-md);
	border-bottom: 1px dashed var(--gray-300);

	.name {
		font-weight: 600;
		font-size: var(--text-md);
		color: var(--gray-800);
		span {
			margin-left: var(--padding-sm);
			color: var(--gray-600);
			font-family: monospace;
		}
	}

	a:hover {
		text-decoration: none;
		color: var(--gray-900);
	}

	.llm {
		margin-left: auto;
	}

	.date,
	.llm {
		font-size: var(--text-xs);
		color: var(--gray-500);
	}

	.separator {
		color: var(--gray-400);
	}

	.status {
		font-size: var(--text-xs);
		padding: 3px var(--padding-sm);
		margin: 0;
	}

	.reasoning-effort {
		margin-left: var(--padding-xs);
		font-family: monospace;
	}
}

.instruction {
	color: var(--gray-700);
	padding: 0;
	margin: 0;
}

.detail-container {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--padding-md);
}

.session-viewer:last-child {
	margin-bottom: 25vh;
}
</style>
