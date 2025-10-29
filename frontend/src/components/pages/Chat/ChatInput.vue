<template>
	<div
		class="border border-gray-200 rounded-full p-2 flex items-center gap-2 bg-white"
		style="box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.06), 0px 1px 2px rgba(0, 0, 0, 0.08)"
	>
		<input
			v-model="message"
			type="text"
			placeholder="Ask..."
			:disabled="disabled || loading"
			@keyup.enter="handleSend"
			class="border-none outline-none rounded-full w-full active:outline-none focus:outline-none focus:ring-0 text-md"
		/>
		<button
			@click="handleSend"
			:disabled="disabled || loading || !message.trim()"
			class="bg-gray-900 rounded-full p-1.5 cursor-pointer"
		>
			<SendIcon class="text-white" />
		</button>
	</div>
</template>

<script setup>
import { ref } from "vue";
import SendIcon from "./SendIcon.vue";

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
	if (props.loading || props.disabled || !message.value) return;

	emit("send", message.value);
	message.value = "";
};
</script>
