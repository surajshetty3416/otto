<template>
	<div
		class="border border-gray-200 rounded-full p-2 flex items-center gap-2 bg-white/75 backdrop-blur-lg"
		style="box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.06), 0px 1px 2px rgba(0, 0, 0, 0.08)"
	>
		<input
			v-model="message"
			type="text"
			placeholder="Ask..."
			:disabled="disabled || loading"
			@keyup.enter="handleSend"
			class="border-none outline-none rounded-full w-full active:outline-none focus:outline-none focus:ring-0 text-md bg-transparent"
		/>
		<button
			@click="showSettingsDialog"
			class="hover:bg-gray-100 rounded-full p-1.5 cursor-pointer"
		>
			<Settings class="w-6 h-6 text-gray-800" stroke-width="1.25" />
		</button>
		<button @click="handleSend" class="bg-gray-900 rounded-full p-1.5 cursor-pointer">
			<ChevronUp class="w-6 h-6 text-white" />
		</button>
	</div>
</template>

<script setup>
import { ChevronUp, Settings } from "lucide-vue-next";
import { ref } from "vue";
import { toast } from "vue-sonner";

const props = defineProps({
	loading: {
		type: Boolean,
		default: false,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["send"]);

const message = ref("");

const handleSend = () => {
	message.value = message.value.trim();
	emit("send", message.value);
	message.value = "";
};

function showSettingsDialog() {
	toast.info("Implement this!");
}
</script>
