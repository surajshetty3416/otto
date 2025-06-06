<script setup>
import { format_date, get_link } from "../utils";
import Link from "./Link.vue";
import ContentViewer from "./ContentViewer.vue";

const props = defineProps({
	index: { type: Number, required: true },
	scrapbook: { type: Object, required: true },
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
		<ContentViewer :value="scrapbook.content" />
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
		color: var(--gray-400);
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
}

.scrapbook:last-child {
	border-bottom: none;
	padding-bottom: 0;
	margin-bottom: 0;
}
</style>
