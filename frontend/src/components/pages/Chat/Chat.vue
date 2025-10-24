<template>
	<div class="w-screen h-screen flex items-center justify-center">
		<div style="width: 768px" class="border-l border-r border-gray-200 h-full relative">
			<ChatMessages :messages="messages" />
			<ChatInput :loading="isLoading" @send="handleSend" class="w-full absolute bottom-2" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { api } from "@/client";
import type { RealtimeChatMessage, SessionItem } from "@/client/generated.types";
import router from "@/router";
import { assert } from "@/utils";
import { computed, onMounted, onUnmounted, ref } from "vue";
import ChatInput from "./ChatInput.vue";
import { getUserMessage } from "./utils";
import ChatMessages from "./ChatMessages.vue";
import socket from "@/socket";

// sanity check to avoid duplicates
const received = new Set<string>();

const props = defineProps<{
	chatId?: string;
}>();

const isNew = computed(() => !!props.chatId);
const assistant = "5t44lus4lh"; // dummy for now
const isLoading = ref(false);
const messages = ref<SessionItem[]>([]);

async function handleSend(query: string) {
	isLoading.value = true;
	if (isNew.value) {
		const chatId = await api.chat.new_chat({ assistant });
		await router.push({ name: "Chat", params: { chatId } });
	}
	appendUserMessage(query);

	assert(props.chatId, "chatId is required");
	await api.chat.send_query({ chat_id: props.chatId, query });
	isLoading.value = false;
}

function appendUserMessage(query: string) {
	messages.value.push(getUserMessage(query));
}

function handleRealtimeMessage(message: RealtimeChatMessage) {
	if (message.chat_id !== props.chatId) return;
	if (received.has(message.id)) return;

	received.add(message.id);
	switch (message.type) {
		case "chunk":
			break;
		case "item":
			break;
		case "request":
			break;
		case "tool-execution-complete":
			break;
		case "tool-execution-update":
			break;
		case "error":
			break;
	}
}

onMounted(() => {
	socket.on("otto.chat.api", handleRealtimeMessage);
});
onUnmounted(() => {
	socket.off("otto.chat.api", handleRealtimeMessage);
});

socket.on("chat", (message) => {
	console.log(message);
});
</script>
