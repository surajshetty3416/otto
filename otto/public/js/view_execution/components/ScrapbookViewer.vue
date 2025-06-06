<script setup>
import { computed } from "vue";
import { format_date, get_link } from "../utils";
import Link from "./Link.vue";
import ObjectViewer from "./ObjectViewer.vue";

const props = defineProps({
	index: { type: Number, required: true },
	scrapbook: { type: Object, required: true },
});

const content = computed(() => {
	try {
		const content = JSON.parse(props.scrapbook.content);
		delete content.explanation;
		return content;
	} catch {
		return props.scrapbook.content;
	}
});

const explanation = computed(() => {
	try {
		return JSON.parse(props.scrapbook.content).explanation;
	} catch {
		return "";
	}
});

const content_style = computed(() => {
	if (!explanation.value) return "";

	return "border-bottom: 1px solid var(--gray-200);";
});
</script>

<template>
	<div class="scrapbook">
		<div class="header">
			<p class="index" title="Index">{{ index + 1 }}.</p>
			<span class="separator">·</span>
			<Link
				:title="`Scrapbook: ${scrapbook.name}`"
				:value="scrapbook.name"
				:link="get_link('Otto Scrapbook', scrapbook.name)"
				class="scrapbook-link"
			/>
			<span class="separator">·</span>
			<Link
				:title="`Tool: ${scrapbook.tool_slug}`"
				:value="scrapbook.tool_slug"
				:link="get_link('Otto Tool', scrapbook.tool)"
				class="tool-link"
			/>
			<p class="created" :title="`Created: ${scrapbook.creation}`">
				{{ format_date(scrapbook.creation) }}
			</p>
		</div>
		<div class="content">
			<ObjectViewer
				class="content-object"
				:style="content_style"
				v-if="typeof content === 'object' && Object.keys(content).length > 0"
				:object="content"
			/>
			<pre
				v-else-if="typeof content !== 'object' && content"
				class="content-regular"
				:style="content_style"
				>{{ content }}</pre
			>
			<p v-else class="content-json">No content</p>

			<p
				v-if="explanation"
				title="Explanation given by LLM for tool use"
				class="explanation"
			>
				{{ explanation }}
			</p>
		</div>
	</div>
</template>
<style scoped>
.scrapbook {
	padding-bottom: var(--padding-md);
	margin-bottom: var(--padding-md);
	border-bottom: 1px dashed var(--gray-200);

	.header {
		display: flex;
		align-items: center;
		gap: var(--padding-sm);
		margin-bottom: var(--padding-xs);
	}

	.index,
	.tool-link,
	.scrapbook-link,
	.created {
		color: var(--gray-500);
		font-size: var(--text-xs);
		font-family: monospace;
		margin: 0;
		padding: 0;
	}

	.separator {
		color: var(--gray-300);
	}

	.index {
		font-weight: 600;
	}

	.created {
		margin-left: auto;
	}

	pre {
		margin: 0;
		padding: 0;
		overflow-x: auto;
		white-space: pre;
	}

	.content {
		border: 1px solid var(--gray-200);

		.content-regular,
		.content-object {
			padding: var(--padding-xs);
		}

		.content-regular {
			color: var(--gray-700);
		}

		.explanation {
			padding: 0;
			margin: 0;
			font-size: var(--text-xs);
			color: var(--gray-600);
			padding: var(--padding-xs);
			background-color: var(--gray-50);
		}
	}
}

.scrapbook:last-child {
	border-bottom: none;
	padding-bottom: 0;
	margin-bottom: 0;
}
</style>
