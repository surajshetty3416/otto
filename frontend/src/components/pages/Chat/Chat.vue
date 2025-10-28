<template>
	<div class="w-screen h-screen flex items-center justify-center flex-col">
		<!-- Header -->
		<div class="border-b h-14 w-full p-4 flex items-center justify-between mb-4">
			<h1 class="text-xl font-bold">Otto Chat</h1>
			<LoadingIndicator
				v-if="isLoading || isStreaming || waitingForStream"
				class="w-5 h-5"
			/>
		</div>

		<!-- Messages -->
		<div style="width: 768px" class="border-l border-r border-gray-200 h-full relative">
			<ChatMessages :messages="messages" />
			<ChatInput :loading="isLoading" @send="handleSend" class="w-full absolute bottom-2" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { api } from "@/client";
import type { RealtimeChatMessage, SessionItem, TextContentChunk } from "@/client/generated.types";
import LoadingIndicator from "@/components/fui/LoadingIndicator.vue";
import router from "@/router";
import socket from "@/socket";
import { assert } from "@/utils";
import { computed, onMounted, onUnmounted, provide, reactive, readonly, ref } from "vue";
import ChatInput from "./ChatInput.vue";
import ChatMessages from "./ChatMessages.vue";
import type { StreamContext } from "./types";
import { getUserSessionItem, handleContentChunk, handleItem, streamContextKey } from "./utils";

// sanity check to avoid duplicates
const received = new Set<string>();
const props = defineProps<{
	chatId?: string;
}>();

const isNew = computed(() => !props.chatId);
const assistant = "1rv777j9m3"; // dummy for now
const isLoading = ref(false); // true if request is being sent
const isStreaming = ref(false); // true if chat is streaming
const waitingForStream = ref(false); // true if waiting for stream to start
const messages = reactive<SessionItem[]>([]);
const streamContext = ref<StreamContext | null>(null);
provide(streamContextKey, readonly(streamContext));

async function handleSend(query: string) {
	isLoading.value = true;
	if (isNew.value) {
		const chatId = await api.chat.new_chat({ assistant });
		await router.replace({ name: "Chat", params: { chatId } });
	}
	appendUserMessage(query);

	assert(props.chatId, "chatId is required");
	await api.chat.send_query({ chat_id: props.chatId, query });
	isLoading.value = false;
	waitingForStream.value = true;
}

function appendUserMessage(query: string) {
	messages.push(getUserSessionItem(query));
}

function handleRealtimeMessage(message: RealtimeChatMessage) {
	if (window.is_dev_mode) console.log(message);

	waitingForStream.value = false;
	setStreamContext(message);

	if (message.chat_id !== props.chatId) return;
	if (received.has(message.id)) return;

	received.add(message.id);
	switch (message.type) {
		case "chunk":
			if (message.data.type === "system") handleSystemChunk(message.data);
			else handleContentChunk(message.data, messages);
			break;
		case "item":
			handleItem(message.data, messages);
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

function setStreamContext(message: RealtimeChatMessage) {
	if (message.type !== "chunk") {
		streamContext.value = null;
		return;
	}

	const chunk = message.data;
	if (!streamContext.value) {
		streamContext.value = {
			itemId: chunk.item_id,
			chunkType: chunk.type,
		};
		return;
	}

	if (chunk.item_id !== streamContext.value.itemId) streamContext.value.itemId = chunk.item_id;
	if (chunk.type !== streamContext.value.chunkType) streamContext.value.chunkType = chunk.type;
}

function handleSystemChunk(chunk: TextContentChunk) {
	switch (chunk.message) {
		case "start":
			isStreaming.value = true;
			break;
		case "end":
			isStreaming.value = false;
			break;
	}
}

onMounted(async () => {
	socket.on("otto.api.chat", handleRealtimeMessage);
	if (isNew.value) return;

	for (const message of await api.chat.load_chat({ chat_id: props.chatId! })) {
		messages.push(message);
	}
});
onUnmounted(() => {
	socket.off("otto.api.chat", handleRealtimeMessage);
});

/**
 * Stack:
 * - [x] handled important streaming types
 * - [ ] complete handling of different content types
 * 	- [ ] agent responses:
 * 		- [ ] handle tool use responses (silent tools, hide tool use in user config)
 * 		- [ ] ui improvements in thinking blocks
 * 	- [ ] user inputs (if markdown detected, syntax highlight as markdown)
 * 	- [ ] add permission request handling (maintain pending requests separately append on receiving)
 * - [ ] error handling
 * - [ ] add support for images and pdfs (create file and do something don't append file to chat (very heavy))
 * 
 * all messages should have an (i) button, on clicking the i button the ui
 * should show sessionitem details, all agent responses should have a thumbs up
 * and down button (this logs feedback) 
 * 
 * TODO: Plan for assistant implementation:
 *
 * handle the realtime messages
 *
 * on chunk message append dummy item which will be filled out with the values
 * from the actual item when the actual item is received
 *
 * on tool execution changes indicate completion of tool calls, on complete resume chat
 *
 * on request show a request block which on click should call the permission endpoints
 *
 * on error show a toast or something to indicate the error
 *
 * - build out the chat interface for the dummy assistant
 * - complete the new chat page, on user query move input to the bottom and show query message
 * - add sidebar, auto set sidebar title (from user message, assistant title or autogen)
 * - add support for images and pdfs (create file and do something don't append file to chat (very heavy))
 * - add support for agent selection
 * - create and experiment with framework assistant
 * - experiment with ui gen
 */
</script>
