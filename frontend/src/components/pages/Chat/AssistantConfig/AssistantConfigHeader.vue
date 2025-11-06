<template>
	<div class="p-4 mb-4 flex items-baseline justify-between">
		<h3 class="text-lg font-semibold" title="Assistant name">
			{{ assistant.title }}
			<span
				title="Unique assistant identifier"
				class="font-mono text-gray-500 ml-2 text-xs font-medium"
				>{{ assistant.name }}</span
			>
		</h3>
		<button
			@click="open = false"
			class="outline-none focus:ring-2 ring-gray-300 rounded-md p-1 opacity-70 hover:opacity-100 transition-opacity"
		>
			<X class="w-4 h-4" stroke-width="1.5" />
			<span class="sr-only">Close</span>
		</button>
	</div>
</template>
<script lang="ts" setup>
import type { Assistant } from "@/client/generated.types";
import { X } from "lucide-vue-next";

const open = defineModel<boolean>({ required: true });
defineProps<{ assistant: Assistant }>();
</script>
