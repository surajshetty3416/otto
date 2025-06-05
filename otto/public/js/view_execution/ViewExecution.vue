<script setup>
import { onMounted, ref, reactive } from "vue";
import Detail from "./components/Detail.vue";
import SectionContainer from "./components/SectionContainer.vue";
import { link_icon, calculateStats } from "./utils";

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

function get_link(doctype, name) {
	return frappe.utils.get_form_link(doctype, name);
}

function format_date(datetimeStr) {
	if (!datetimeStr) return "N/A";
	return new Date(datetimeStr).toLocaleString();
}

function format_duration(duration) {
	return frappe.utils.get_formatted_duration(duration);
}

function format_number(number) {
	return number.toLocaleString();
}

async function fetchData() {
	// Fetch Execution and Related Data
	const executionPromise = frappe.db
		.get_doc("Otto Execution", props.executionName)
		.then(async (_doc) => {
			const _info = await frappe.call({
				method: "otto.otto.doctype.otto_task.otto_task.get_exec_view_info",
				args: { task_name: _doc.task },
			});

			doc.value = _doc;
			execution.value = JSON.parse(_doc.execution);
			stats.value = calculateStats(execution.value);
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
			fields: ["name", "content", "tool"],
		})
		.then((_scrapbooks) => {
			scrapbooks.value = _scrapbooks;
			loading.scrapbook = false;
		})
		.catch((e) => {
			errors.scrapbook = e.message || "Failed to load scrapbooks.";
		});

	await Promise.all([executionPromise, scrapbookPromise]);
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
	<div class="execution-viewer">
		<!-- Header -->
		<div class="detail-header" v-if="doc">
			<a class="name" :href="get_link('Otto Execution', doc.name)">
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
		<SectionContainer title="" :isLoading="loading.execution" :error="errors.execution">
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

		<!-- 2. Execution Stats -->
		<SectionContainer title="Stats" :isLoading="loading.execution" :error="errors.execution">
			<div class="detail-container">
				<Detail label="Cost" :value="`$${stats.cost}`" />
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

		<!-- 3. Scrapbook -->
		<SectionContainer
			title="Scrapbook"
			:isLoading="loading.scrapbook"
			:error="errors.scrapbook"
			>scrapbook</SectionContainer
		>

		<!-- 4. Exchange -->
		<SectionContainer title="Exchange" :isLoading="loading.execution" :error="errors.execution"
			>exchange</SectionContainer
		>

		<!-- 5. Instruction -->
		<SectionContainer
			title="Instruction"
			:isLoading="loading.execution"
			:error="errors.execution"
			>instruction</SectionContainer
		>
	</div>
</template>
<
<style scoped>
.detail-header {
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
			font-family: var(--font-mono);
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
		padding: 0.15rem 0.5rem;
		border-radius: var(--border-radius-sm);
	}
}

.detail-container {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--padding-md);
}
</style>
