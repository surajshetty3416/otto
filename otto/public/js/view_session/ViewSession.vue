<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import Detail from "./components/Detail.vue";
import ExchangeViewer from "./components/SessionViewer.vue";
import PreViewer from "./components/PreViewer.vue";
import ScrapbookViewer from "./components/ScrapbookViewer.vue";
import SectionContainer from "./components/SectionContainer.vue";
import StatsViewer from "./components/StatsViewer.vue";
import { format_date, get_link, get_stats, link_icon } from "./utils";

const props = defineProps({
	sessionName: {
		type: String,
		required: true,
	},
});

const doc = ref(null);
const session = ref(null);
const stats = ref(null);
const scrapbooks = ref(null);
const info = ref(null);
const loading = reactive({
	session: true,
	scrapbook: true,
});
const errors = reactive({
	session: null,
	scrapbook: null,
});

const exchange_sequence = computed(() => {
	if (!session.value) return [];
	const items = [];
	let current_id = session.value.first;
	while (current_id) {
		const item = session.value.items[current_id];
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
	// Fetch Session and Related Data
	const sessionPromise = frappe.db
		.get_doc("Otto Session", props.sessionName)
		.then((_doc) => {
			doc.value = _doc;
			if (_doc.session) {
				session.value = JSON.parse(_doc.session);
				stats.value = get_stats(session.value);
			}

			return frappe.call({
				method: "otto.otto.doctype.otto_task.otto_task.get_exec_view_info",
				args: { task_name: _doc.task, llm_name: _doc.llm },
			});
		})
		.then((_info) => {
			info.value = _info.message;
			loading.session = false;
		})
		.catch((e) => {
			loading.session = false;
			errors.session = e.message || "Failed to load session.";
		});

	// Fetch Scrapbook
	const scrapbookPromise = frappe.db
		.get_list("Otto Scrapbook", {
			filters: { session: props.sessionName },
			fields: ["name", "content", "tool", "creation"],
		})
		.then((_scrapbooks) => {
			scrapbooks.value = _scrapbooks;
			loading.scrapbook = false;
		})
		.catch((e) => {
			loading.scrapbook = false;
			errors.scrapbook = e.message || "Failed to load scrapbooks.";
		});

	await Promise.all([sessionPromise, scrapbookPromise]);
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
</script>

<template>
	<div class="session-viewer">
		<!-- 0. Header -->
		<div class="detail-header" v-if="doc">
			<a class="name" :href="get_link('Otto Session', doc.name)" target="_blank">
				Session <span>{{ doc.name }}</span> <span v-html="link_icon"></span
			></a>
			<div class="date">{{ format_date(doc.creation) }}</div>
			<span class="separator">·</span>
			<div class="status" :style="get_status_style(doc.status)">
				{{ doc.status }}
			</div>
		</div>
		<div v-else class="detail-header">Loading...</div>

		<!-- 1. Session Details -->
		<SectionContainer
			title=""
			label=""
			:isLoading="loading.session"
			:error="errors.session"
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
						v-if="doc.target_doctype"
						label="Target"
						:value="`${doc.target_doctype} - ${doc.target}`"
						:link="get_link(doc.target_doctype, doc.target)"
					/>
					<Detail label="Event" :value="doc.event" />
					<Detail
						title="LLM used to handle this task"
						label="LLM"
						:value="info.llm_title"
						:link="get_link('Otto LLM', doc.llm)"
					/>
					<Detail
						title="Reasoning effort used to handle task"
						label="Reasoning"
						:value="doc.reasoning_effort"
					/>
				</div>
			</div>
		</SectionContainer>

		<!-- Stats -->
		<SectionContainer
			v-if="stats"
			title="Stats: metadata about the session run"
			label="Stats"
			:isLoading="loading.session"
			:error="errors.session"
		>
			<StatsViewer :stats="stats" :info="info" />
		</SectionContainer>

		<!-- Error -->
		<SectionContainer
			v-if="doc?.reason"
			title="Error: reason for the session failure"
			label="Error"
			:show="true"
			:isLoading="loading.session"
			:error="errors.session"
		>
			<PreViewer :value="doc.reason" />
		</SectionContainer>

		<!-- Scrapbook -->
		<SectionContainer
			v-if="scrapbooks && scrapbooks.length > 0"
			title="Scrapbook: mocked tool args or other logs recorded in Otto Scrapbook"
			label="Scrapbook"
			:isLoading="loading.scrapbook"
			:error="errors.scrapbook"
		>
			<template v-for="(book, index) in scrapbooks" :key="book.name">
				<ScrapbookViewer v-if="book" :scrapbook="book" :index="index" />
			</template>
		</SectionContainer>

		<!-- Exchange -->
		<SectionContainer
			v-if="session"
			title="Session: session sequence of the task"
			label="Session"
			:isLoading="loading.session"
			:error="errors.session"
		>
			<div v-if="session">
				<ExchangeViewer
					v-for="(item, index) in exchange_sequence"
					:key="item.id"
					:item="item"
					:index="index"
				/>
			</div>
		</SectionContainer>

		<!-- Instruction -->
		<SectionContainer
			v-if="doc?.instruction"
			title="Instruction: system prompt used to instruct the LLM on how to execute the task"
			label="Instruction"
			:show="false"
			:isLoading="loading.session"
			:error="errors.session"
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
