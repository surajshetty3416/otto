<script setup>
import { onMounted, ref, reactive } from "vue";
import SectionContainer from "./components/SectionContainer.vue";
import { calculateStats } from "./utils";

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
const tool_info = ref(null);
const loading = reactive({
	execution: true,
	scrapbook: true,
});
const errors = reactive({
	execution: null,
	scrapbook: null,
});

async function fetchData() {
	// Fetch Execution and Related Data
	const executionPromise = frappe.db
		.get_doc("Otto Execution", props.executionName)
		.then(async (_doc) => {
			const _tool_info = await frappe.call({
				method: "otto.otto.doctype.otto_task.otto_task.get_tool_info",
				args: { task_name: _doc.task },
			});

			doc.value = _doc;
			execution.value = JSON.parse(_doc.execution);
			stats.value = calculateStats(execution.value);
			tool_info.value = _tool_info.message;
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

onMounted(async () => await fetchData());
</script>

<template>
	<div class="execution-viewer">
		<!-- 1. Execution Details -->
		<SectionContainer title="" :isLoading="loading.execution" :error="errors.execution"
			>details</SectionContainer
		>

		<!-- 2. Execution Stats -->
		<SectionContainer title="Stats" :isLoading="loading.execution" :error="errors.execution"
			>stats</SectionContainer
		>

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

<style lang="scss"F>
/* Fallback variables if Frappe's are not available or for easier theming */
:root {
	--font-family-sans-serif: sans-serif;
	--font-family-mono: monospace;
	--text-color: #333;
	--text-light: #555;
	--text-muted: #777;
	--text-on-dark-bg: #f8f9fa;
	--heading-color: #222;
	--primary-color: #007bff;
	--border-color: #dee2e6;
	--border-radius: 0.25rem;
	--border-radius-sm: 0.2rem;
	--border-radius-md: 0.3rem;
	--border-radius-pill: 50rem;
	--fg-color: #fff;
	--fg-color-alt: #f8f9fa;
	--control-bg: #f8f9fa;
	--subtle-bg: #e9ecef; // for headers
	--subtle-bg-hover: #dadce0;
	--dark-bg-color: #212529;

	--padding-xs: 0.25rem;
	--padding-sm: 0.5rem;
	--padding-md: 0.75rem;
	--padding-lg: 1rem;
	--padding-xl: 1.5rem;

	--margin-xs: 0.25rem;
	--margin-sm: 0.5rem;
	--margin-md: 0.75rem;
	--margin-lg: 1rem;
	--margin-xl: 1.5rem;

	--spacing-xs: 0.25rem;
	--spacing-sm: 0.5rem;
	--spacing-md: 1rem;
	--spacing-lg: 1.5rem;
	--spacing-xl: 2rem;

	--text-xs: 0.75rem;
	--text-sm: 0.875rem;
	--text-base: 1rem;
	--text-md: 1.125rem;
	--text-lg: 1.25rem;
	--text-xl: 1.5rem;

	--font-weight-normal: 400;
	--font-weight-semibold: 600;
	--font-weight-bold: 700;

	--white: #fff;
	--gray-100: #f8f9fa;
	--gray-200: #e9ecef;
	--gray-300: #dee2e6;

	--red-100: #fde8e8;
	--red-300: #f5c6cb;
	--red-500: #dc3545;
	--text-danger: var(--red-500);

	--green-500: #28a745;
	--blue-500: #007bff;
	--yellow-500: #ffc107;
}
</style>
