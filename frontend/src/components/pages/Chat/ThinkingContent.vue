<template>
	<div class="bg-gray-200 p-2 w-fit rounded-sm">
		<div class="flex items-center gap-2 cursor-pointer select-none" @click="isOpen = !isOpen">
			<ChevronDown v-if="isOpen" class="h-4 w-4 text-gray-600 flex-shrink-0" />
			<ChevronRight v-else class="h-4 w-4 text-gray-600 flex-shrink-0" />
			<p v-if="!isOpen" class="italic text-gray-600 text-sm">Thought</p>
		</div>
		<p v-if="isOpen" class="italic text-gray-800 text-base mt-1">
			{{ content.text }}
		</p>
	</div>
</template>
<script setup lang="ts">
import type { ThinkingContent } from "@/client/generated.types";
import { ChevronDown, ChevronRight } from "lucide-vue-next";
import { computed, inject, ref, watch } from "vue";
import { sessionItemKey, streamContextKey } from "./utils";

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
