<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import Detail from "./components/Detail.vue";
import ExchangeViewer from "./components/ExchangeViewer.vue";
import PreViewer from "./components/PreViewer.vue";
import ScrapbookViewer from "./components/ScrapbookViewer.vue";
import SectionContainer from "./components/SectionContainer.vue";
import {
	format_date,
	format_duration,
	format_number,
	get_link,
	get_stats,
	link_icon,
} from "./utils";

const props = defineProps({
	executionName: {
		type: String,
		required: true,
	},
});

const doc = ref(null);
const execution = ref(null);
const stats = ref(null);
const scrapbooks = ref(null);
const info = ref(null);
const loading = reactive({
	execution: true,
	scrapbook: true,
});
const errors = reactive({
	execution: null,
	scrapbook: null,
});

const exchange_sequence = computed(() => {
	if (!execution.value) return [];
	const items = [];
	let current_id = execution.value.first;
	while (current_id) {
		const item = execution.value.items[current_id];
		if (!item) break;
		items.push(item);

		for (const content of item.content) {
			if (content.type !== "tool_use") continue;
			const tool_name = info.value.slug_map[content.name];
			content.tool = info.value.tool_map[tool_name];
		}

		if (item.next && item.next.length > 0) {
			const next_index = item.selected_next || 0;
			current_id = item.next[next_index];
		} else {
			current_id = null;
		}
	}
	return items;
});

async function fetchData() {
	// Fetch Execution and Related Data
	const executionPromise = frappe.db
		.get_doc("Otto Execution", props.executionName)
		.then((_doc) => {
			doc.value = _doc;
			execution.value = JSON.parse(_doc.execution);
			stats.value = get_stats(execution.value);

			return frappe.call({
				method: "otto.otto.doctype.otto_task.otto_task.get_exec_view_info",
				args: { task_name: _doc.task },
			});
		})
		.then((_info) => {
			info.value = _info.message;
			loading.execution = false;
		})
		.catch((e) => {
			errors.execution = e.message || "Failed to load execution.";
		});

	// Fetch Scrapbook
	const scrapbookPromise = frappe.db
		.get_list("Otto Scrapbook", {
			filters: { execution: props.executionName },
			fields: ["name", "content", "tool", "creation"],
		})
		.then((_scrapbooks) => {
			scrapbooks.value = _scrapbooks;
			loading.scrapbook = false;
		})
		.catch((e) => {
			errors.scrapbook = e.message || "Failed to load scrapbooks.";
		});

	await Promise.all([executionPromise, scrapbookPromise]);
	for (const book of scrapbooks.value) {
		book.tool_slug = info.value.tool_map[book.tool].slug;
	}
}

function get_status_style(status) {
	if (status === "Pending") return "color: var(--gray-700); background-color: var(--gray-100);";
	if (status === "Running") return "color: var(--blue-700); background-color: var(--blue-50);";
	if (status === "Success") return "color: var(--green-700); background-color: var(--green-50);";
	if (status === "Failure") return "color: var(--red-700); background-color: var(--red-50);";
}

onMounted(async () => await fetchData());

/**
 * TODO:
 * - execution comparison
 * - highlight instruction, json, etc
 * - feedback section
 * - show args only if not super long
 * - show result if not super long
 * - if error show reason
 * - handle no executions
 * - allow show and hide tool use body
 */
</script>

<template>
	<div class="execution-viewer">
		<!-- 0. Header -->
		<div class="detail-header" v-if="doc">
			<a class="name" :href="get_link('Otto Execution', doc.name)" target="_blank">
				Execution <span>{{ doc.name }}</span> <span v-html="link_icon"></span
			></a>
			<div class="date">{{ format_date(doc.creation) }}</div>
			<span class="separator">·</span>
			<div class="status" :style="get_status_style(doc.status)">
				{{ doc.status }}
			</div>
		</div>
		<div v-else class="detail-header">Loading...</div>

		<!-- 1. Execution Details -->
		<SectionContainer
			title=""
			label=""
			:isLoading="loading.execution"
			:error="errors.execution"
		>
			<div>
				<!-- Details -->
				<div class="detail-container">
					<Detail
						label="Task"
						:value="info.task_title"
						:link="get_link('Otto Task', doc.task)"
					/>
					<Detail
						label="Target"
						:value="`${doc.target_doctype} - ${doc.target}`"
						:link="get_link(doc.target_doctype, doc.target)"
					/>
					<Detail label="Event" :value="doc.event" />
					<Detail
						label="LLM"
						:value="info.llm_title"
						:link="get_link('Otto LLM', doc.llm)"
					/>
				</div>
			</div>
		</SectionContainer>

		<!-- 2. Scrapbook -->
		<SectionContainer
			title="Scrapbook: mocked tool args or other logs recorded in Otto Scrapbook"
			label="Scrapbook"
			:isLoading="loading.scrapbook"
			:error="errors.scrapbook"
			v-show="scrapbooks && scrapbooks.length > 0"
		>
			<template v-for="(book, index) in scrapbooks" :key="book.name">
				<ScrapbookViewer v-if="book" :scrapbook="book" :index="index" />
			</template>
		</SectionContainer>

		<!-- 3. Exchange -->
		<SectionContainer
			title="Execution: execution sequence of the task"
			label="Execution"
			:isLoading="loading.execution"
			:error="errors.execution"
		>
			<div v-if="execution">
				<ExchangeViewer
					v-for="(item, index) in exchange_sequence"
					:key="item.id"
					:item="item"
					:index="index"
				/>
			</div>
		</SectionContainer>

		<!-- 4. Stats -->
		<SectionContainer
			title="Stats: metadata about the execution run"
			label="Stats"
			:isLoading="loading.execution"
			:error="errors.execution"
		>
			<div class="detail-container">
				<Detail label="Cost" :value="`$${stats.cost.toFixed(6)}`" />
				<Detail
					label="Duration"
					:value="format_duration(stats.duration)"
					:title="`${stats.duration} seconds`"
				/>
				<Detail label="LLM Calls" :value="format_number(stats.llm_calls)" />
				<Detail
					label="Max Input Tokens"
					:value="format_number(stats.max_input_tokens) + ' tok'"
				/>
				<Detail
					label="Max Output Tokens"
					:value="format_number(stats.max_output_tokens) + ' tok'"
				/>
				<Detail
					label="Total Input Tokens"
					:value="format_number(stats.total_input_tokens) + ' tok'"
				/>
				<Detail
					label="TotalOutput Tokens"
					:value="format_number(stats.total_output_tokens) + ' tok'"
				/>
			</div>
		</SectionContainer>

		<!-- 5. Instruction -->
		<SectionContainer
			v-if="doc?.instruction"
			title="Instruction: system prompt used to instruct the LLM on how to execute the task"
			label="Instruction"
			:show="false"
			:isLoading="loading.execution"
			:error="errors.execution"
		>
			<PreViewer :value="doc.instruction" />
		</SectionContainer>
	</div>
</template>
<style scoped>
.detail-header {
	position: sticky;
	top: calc(var(--navbar-height) + var(--page-head-height) + 1px);
	background-color: var(--white);
	z-index: 20;

	display: flex;
	align-items: center;
	gap: var(--padding-md);
	padding: var(--padding-xs) var(--padding-md);
	border-bottom: 1px dashed var(--gray-300);

	.name {
		font-weight: 600;
		font-size: var(--text-sm);
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

	.date {
		margin-left: auto;
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
</style>
