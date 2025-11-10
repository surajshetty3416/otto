<template>
	<!-- Toggle Thought -->
	<CollapsedContentToggle v-model="isOpen">
		<Brain class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
	</CollapsedContentToggle>

	<ContentContainer v-if="isOpen || isStreaming">
		<!-- Thought Header -->
		<div
			class="flex items-center justify-between border-b border-gray-300 p-1.5 cursor-pointer"
			@click.stop="isOpen = false"
			title="Hide Thought"
		>
			<h3 class="text-gray-800 text-xs font-semibold flex items-center gap-1.5">
				<Brain class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
				{{ isStreaming ? "Thinking..." : "Thought" }}
			</h3>
			<button @click="isOpen = false">
				<X class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
			</button>
		</div>

		<!-- Thought Content -->
		<Markdown
			class="p-1.5 last:pb-0 text-gray-700"
			style="font-style: italic; font-size: 85%"
			>{{ content.text }}</Markdown
		>
	</ContentContainer>
</template>
<script setup lang="ts">
import type { SessionItem, ThinkingContent } from "@/client/generated.types";
import { Brain, X } from "lucide-vue-next";
import { computed, inject, ref } from "vue";
import CollapsedContentToggle from "./CollapsedContentToggle.vue";
import ContentContainer from "./ContentContainer.vue";
import Markdown from "./Markdown.vue";
import { streamContextKey } from "./utils";

const streamContext = inject(streamContextKey);

const props = defineProps<{
	item: SessionItem;
	content: ThinkingContent;
}>();

const isOpen = ref(false);
const isStreaming = computed(() => {
	if (!streamContext?.isStreamingResponse) return false;
	const message = streamContext?.messages.at(-1);
	if (message?.type !== "chunk") return false;

	const chunk = message?.data;
	return chunk?.type === "thinking" && chunk?.item_id === props.item.id;
});
</script>
