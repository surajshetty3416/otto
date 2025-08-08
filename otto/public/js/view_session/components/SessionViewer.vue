<script setup>
import { computed, ref } from "vue";
import { format_date, format_duration, format_number } from "../utils";
import ToolUseViewer from "./ToolUseViewer.vue";
import TextViewer from "./TextViewer.vue";
import ImageViewer from "./ImageViewer.vue";

const props = defineProps({
	index: {
		type: Number,
		required: true,
	},
	item: {
		type: Object,
		required: true,
	},
	has_task: {
		type: Boolean,
		required: true,
	},
});

const show = ref(true);
const isSystem = computed(() => props.item.meta.role === "user");
const cost = computed(() => (props.item.meta.cost ? `$${props.item.meta.cost.toFixed(6)}` : null));
const duration = computed(() => {
	if (props.item.meta.end_time && props.item.meta.start_time) {
		return props.item.meta.end_time - props.item.meta.start_time;
	}

	return null;
});
const role = computed(() => {
	if (props.item.meta.role !== "user") {
		return "llm";
	}

	if (props.has_task) {
		return "system";
	}

	return "user";
});

const duration_str = computed(() => {
	const parts = [];

	if (duration.value) {
		parts.push(`Duration: ${format_duration(duration.value)}`);
	}

	if (props.item.meta.time_to_first_chunk) {
		parts.push(`Time to first chunk: ${format_duration(props.item.meta.time_to_first_chunk)}`);
	}

	if (props.item.meta.inter_chunk_latency) {
		parts.push(`Inter chunk latency: ${format_duration(props.item.meta.inter_chunk_latency)}`);
	}

	if (props.item.meta.output_tokens && duration.value) {
		parts.push(
			`Tokens per second: ${format_number(
				props.item.meta.output_tokens / duration.value
			)} tok/s`
		);
	}

	return parts.join("\n");
});
</script>

<template>
	<div class="session-item-container" :class="{ 'user-item': isSystem, 'llm-item': !isSystem }">
		<div
			class="header"
			:class="{ 'user-header': isSystem && show, 'llm-header': !isSystem && show }"
			@click="show = !show"
		>
			<div class="role" :class="{ 'role-system': isSystem, 'role-llm': !isSystem }">
				{{ role }}
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
		<div class="meta" v-if="!isSystem && show">
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
				<p class="meta-item" :title="duration_str">
					{{ format_duration(duration) }}
				</p>
				<p class="separator">·</p>
				<p class="meta-item" :title="`End Reason: ${item.meta.end_reason}`">
					{{ item.meta.end_reason }}
				</p>
			</div>
		</div>

		<!-- Content List -->
		<div class="content-wrapper" v-if="show">
			<div v-for="(content, index) in item.content" :key="index" class="content-block">
				<!-- Text Block -->
				<TextViewer
					v-if="content.type === 'text'"
					:index="index"
					:value="content.text"
					:is-thinking="false"
				/>

				<!-- Thinking Block -->
				<TextViewer
					v-else-if="content.type === 'thinking'"
					:title="`Thinking block, signature: ${content.signature}`"
					:index="index"
					:value="content.text"
					:is-thinking="true"
				/>

				<ToolUseViewer
					v-else-if="content.type === 'tool_use'"
					title="Tool use block"
					:index="index"
					:content="content"
				/>

				<!-- Image Block -->
				<ImageViewer
					v-else-if="content.type === 'image'"
					:index="index"
					:content="content"
				/>

				<!-- File Block -->
				<div v-else-if="content.type === 'file'">
					<!-- <div class="file-content">
						<p>
							<span class="file-icon">📄</span>
							<span>{{ content.name }}</span>
						</p>
					</div> -->
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.session-item-container {
	border: 1px solid var(--gray-200);
	margin-bottom: var(--padding-md);
	background-color: var(--white);
	overflow: hidden;
}

.session-item-container:last-child {
	margin-bottom: 0;
}

.user-item {
	border-left: 3px solid var(--violet-200);
}

.llm-item {
	border-left: 3px solid var(--teal-200);
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	z-index: 10;

	font-size: var(--text-xs);
	padding: var(--padding-sm);
	font-family: monospace;
	cursor: pointer;

	&:hover {
		background-color: var(--gray-50);
	}

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
		background-color: var(--violet-100);
		color: var(--violet-700);
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

.separator {
	color: var(--gray-300);
}
</style>
