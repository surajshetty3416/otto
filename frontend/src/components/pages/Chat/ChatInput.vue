<template>
	<div
		class="border border-gray-200 rounded-full p-2 flex items-center gap-2 glass-lg"
		style="box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.06), 0px 1px 2px rgba(0, 0, 0, 0.08)"
	>
		<input
			v-model="query"
			type="text"
			placeholder="Ask..."
			:disabled="disabled || loading"
			@keyup.enter="emit('send')"
			class="border-none outline-none rounded-full w-full active:outline-none focus:outline-none focus:ring-0 text-md bg-transparent"
		/>

		<button @click="emit('send')" class="bg-gray-900 rounded-full p-1.5 cursor-pointer">
			<ChevronUp class="w-6 h-6 text-white" />
		</button>
	</div>
</template>

<script setup lang="ts">
import { ChevronUp } from "lucide-vue-next";

defineProps({
	loading: {
		type: Boolean,
		default: false,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	chatId: {
		type: String,
		required: true,
	},
});

const emit = defineEmits(["send"]);
const query = defineModel({ type: String, required: true });
</script>
