<script setup>
import { computed } from "vue";
import { format_date, format_duration, format_number } from "../utils";
import ToolUseViewer from "./ToolUseViewer.vue";

const props = defineProps({
	index: {
		type: Number,
		required: true,
	},
	item: {
		type: Object,
		required: true,
	},
});

const isSystem = computed(() => props.item.meta.role === "user");
const cost = computed(() => (props.item.meta.cost ? `$${props.item.meta.cost.toFixed(6)}` : null));
const duration = computed(() => {
	if (props.item.meta.end_time && props.item.meta.start_time) {
		return props.item.meta.end_time - props.item.meta.start_time;
	}

	return null;
});
</script>

<template>
	<div class="exchange-item-container" :class="{ 'user-item': isSystem, 'llm-item': !isSystem }">
		<div class="header" :class="{ 'user-header': isSystem, 'llm-header': !isSystem }">
			<div class="role" :class="{ 'role-system': isSystem, 'role-llm': !isSystem }">
				{{ isSystem ? "system" : "llm" }}
			</div>
			<div class="header-meta">
				<p :title="`ID: ${item.id}`">{{ item.id.slice(0, 10) }}</p>
				<span class="separator">·</span>
				<p :title="`Timestamp: ${item.meta.timestamp}`">
					{{ format_date(item.meta.start_time || item.meta.timestamp) }}
				</p>
				<span class="separator">·</span>
				<p :title="`Index: ${index + 1}`">#{{ index + 1 }}</p>
			</div>
		</div>

		<!-- Meta Data -->
		<div class="meta" v-if="!isSystem">
			<p
				class="meta-item"
				:title="`Input Tokens: ${item.meta.input_tokens}, Output Tokens:
				${item.meta.output_tokens}`"
			>
				{{ format_number(item.meta.input_tokens) }} /
				{{ format_number(item.meta.output_tokens) }} tok
			</p>
			<p class="separator">·</p>
			<p class="meta-item" :title="`Cost: ${cost}`">
				{{ cost }}
			</p>

			<!-- Right Shifted meta -->
			<div class="right-meta">
				<p class="meta-item" :title="`Duration: ${duration}s`">
					{{ format_duration(duration) }}
				</p>
				<p class="separator">·</p>
				<p class="meta-item" :title="`End Reason: ${item.meta.end_reason}`">
					{{ item.meta.end_reason }}
				</p>
			</div>
		</div>

    <!-- Content List -->
		<div class="content-wrapper">
			<div v-for="(content, index) in item.content" :key="index" class="content-block">
				<!-- Text Block -->
				<div v-if="content.type === 'text'">
					<pre class="content-pre">{{ content.text }}</pre>
				</div>

				<!-- Thinking Block -->
				<div v-else-if="content.type === 'thinking'">
					<details>
						<summary>Thinking</summary>
						<pre class="content-pre">{{ content.text }}</pre>
					</details>
				</div>

				<ToolUseViewer v-else-if="content.type === 'tool_use'" :content="content" />

				<!-- Image Block -->
				<div v-else-if="content.type === 'image'">
					add show, hide image
					<!-- <img
						:src="content.url || content.data"
						alt="image content"
						class="image-content"
					/> -->
				</div>

				<!-- File Block -->
				<div v-else-if="content.type === 'file'">
					<div class="file-content">
						<p>
							<span class="file-icon">📄</span>
							<span>{{ content.name }}</span>
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.exchange-item-container {
	border: 1px solid var(--gray-200);
	margin-bottom: var(--padding-md);
	background-color: var(--white);
	overflow: hidden;
}

.exchange-item-container:last-child {
	margin-bottom: 0;
}

.user-item {
	border-left: 3px solid var(--purple-200);
}

.llm-item {
	border-left: 3px solid var(--teal-200);
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;

	font-size: var(--text-xs);
	padding: var(--padding-sm);
	font-family: monospace;

	.header-meta {
		color: var(--gray-500);
		display: flex;
		align-items: center;
		gap: var(--padding-sm);

		p {
			margin: 0;
			padding: 0;
		}
	}

	.role {
		padding: 3px var(--padding-sm);
		font-weight: 600;
		text-transform: uppercase;
	}

	.role-system {
		background-color: var(--purple-100);
		color: var(--purple-700);
	}

	.role-llm {
		background-color: var(--teal-100);
		color: var(--teal-700);
	}
}

.user-header {
	border-bottom: 1px solid var(--gray-200);
}

.llm-header {
	border-bottom: 1px dashed var(--gray-300);
}

.meta {
	display: flex;
	align-items: center;
	gap: var(--padding-md);

	padding: var(--padding-sm);
	border-bottom: 1px solid var(--gray-200);
	color: var(--gray-500);

	font-family: monospace;
	font-size: var(--text-xs);

	.meta-item {
		display: flex;
		align-items: center;
		gap: var(--padding-sm);
	}

	p {
		margin: 0;
	}

	.right-meta {
		display: flex;
		align-items: center;
		gap: var(--padding-sm);
		margin-left: auto;
	}
}

.content-block {
	padding: var(--padding-sm);
	border-bottom: 1px solid var(--gray-200);
}

.content-block:last-child {
	border-bottom: none;
}

.content-pre {
	white-space: pre-wrap;
	word-wrap: break-word;
	background-color: var(--gray-100);
	padding: var(--padding-sm);
	color: var(--gray-800);
	margin: 0;
	font-family: var(--font-family-mono);
	font-size: var(--text-xs);
}

details {
	margin-top: var(--padding-sm);
}

summary {
	cursor: pointer;
	font-weight: 600;
	color: var(--gray-600);
	font-size: var(--text-xs);
}

.image-content {
	max-width: 100%;
	border: 1px solid var(--gray-200);
}

.file-content {
	display: flex;
	align-items: center;
	gap: var(--padding-sm);
}

.separator {
	color: var(--gray-400);
}
</style>
