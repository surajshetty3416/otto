<template>
	<div class="mb-2">
		<div v-if="isOpen" class="bg-gray-50 rounded-md border border-gray-200">
			<!-- Thought Header -->
			<div
				class="flex items-center justify-between border-b border-gray-200 p-2 cursor-pointer"
				@click.stop="isOpen = false"
				title="Hide Thought"
			>
				<h3 class="text-gray-800 text-sm font-semibold flex items-center gap-2">
					<Brain class="h-4 w-4 text-gray-600 flex-shrink-0" />
					{{ isStreaming ? "Thinking..." : "Thought" }}
				</h3>
				<button @click="isOpen = false">
					<X class="h-4 w-4 text-gray-600 flex-shrink-0" />
				</button>
			</div>

			<!-- Thought Content -->
			<Markdown class="p-2 last:pb-0" style="font-style: italic">{{
				content.text
			}}</Markdown>
		</div>

		<!-- Show Thought -->
		<button
			v-else
			title="Show Thought"
			class="bg-gray-50 border p-2 w-fit rounded-full"
			@click="isOpen = true"
		>
			<Brain class="h-4 w-4 text-gray-600 flex-shrink-0" />
		</button>
	</div>
</template>
<script setup lang="ts">
import type { ThinkingContent } from "@/client/generated.types";
import { Brain, X } from "lucide-vue-next";
import { computed, inject, ref, watch } from "vue";
import { sessionItemKey, streamContextKey } from "./utils";
import Markdown from "./Markdown.vue";

const streamContext = inject(streamContextKey);
const sessionItem = inject(sessionItemKey);

// TODO: styling
// if is streaming show fixed heighted scrolling div a la grok on streaming collapse
// after streaming show an icon (brain) to expand and show thought, show a hide button to collapse

defineProps<{
	content: ThinkingContent;
}>();

const isOpen = ref(false);

const isStreaming = computed(() => {
	return (
		sessionItem?.id === streamContext?.value?.itemId &&
		streamContext?.value?.chunkType === "thinking"
	);
});

watch(streamContext!, (newVal) => {
	if (sessionItem?.id !== streamContext?.value?.itemId || !newVal) return;
	isOpen.value = newVal.chunkType === "thinking";
});
</script>
