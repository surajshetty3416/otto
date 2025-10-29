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
		<div
			class="w-full h-full overflow-y-scroll flex flex-col items-center"
			ref="messagesContainer"
		>
			<div class="border-gray-200 h-full container-ch chat-messages">
				<ChatMessages :messages="messages" />
				<div style="height: 20vh; flex-shrink: 0"></div>
			</div>

			<!-- Input -->
			<div class="fixed bottom-4 w-full container-ch chat-input">
				<ChatInput :loading="isLoading" @send="handleSend" />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { api } from "@/client";
import type {
	PendingRequest,
	RealtimeChatMessage,
	SessionItem,
	TextContentChunk,
	ToolConfig,
} from "@/client/generated.types";
import LoadingIndicator from "@/components/fui/LoadingIndicator.vue";
import router from "@/router";
import socket from "@/socket";
import { assert } from "@/utils";
import { computed, onMounted, onUnmounted, provide, reactive, ref } from "vue";
import ChatInput from "./ChatInput.vue";
import ChatMessages from "./ChatMessages.vue";
import type { StreamContext } from "./types";
import {
	getUserSessionItem,
	handleContentChunk,
	handleItem,
	pendingRequestsKey,
	streamContextKey,
	toolConfigKey,
} from "./utils";

/**
 * When streaming show a spinner above the input about what is going on, e.g.
 * thinking, calling tool, responding, waiting for permission, etc.
 *
 * when showing a list of item pills (thought, tool calls, etc) on clicking open
 * the dialog below and highlight that the item is open.
 */

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
const messagesContainer = ref<HTMLDivElement | null>(null);
const messages = reactive<SessionItem[]>([]);
const streamContext = reactive<StreamContext>({ itemId: "", chunkType: "" });
const list_tools = api.chat.list_tools({ chat_id: props.chatId! }, { auto: false });
const toolConfigs = computed(() => {
	const configs: Record<string, ToolConfig> = {};
	for (const tool of list_tools.data ?? []) {
		configs[tool.slug] = tool;
	}
	return configs;
});
const pendingRequests = reactive<Record<string, PendingRequest>>({});
provide(streamContextKey, streamContext);
provide(toolConfigKey, toolConfigs);
provide(pendingRequestsKey, pendingRequests);

async function handleSend(query: string) {
	isLoading.value = true;
	if (isNew.value) {
		const chatId = await api.chat.new_chat({ assistant });
		await router.replace({ name: "Chat", params: { chatId } });
		await updatePendingRequests();
	}
	appendUserMessage(query);

	assert(props.chatId, "chatId is required");
	await api.chat.send_query({ chat_id: props.chatId, query });
	isLoading.value = false;
	waitingForStream.value = true;
	await list_tools.rerun({ chat_id: props.chatId! });
}

async function handleResume() {
	isLoading.value = true;
	await api.chat.resume_chat({ chat_id: props.chatId! });
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
			return;
		case "item":
			handleItem(message.data, messages);
			return;
		case "request":
			pendingRequests[message.data.tool_use_id] = message.data;
			return;
		case "tool-execution-complete":
			handleToolExecutionComplete();
			return;
		case "tool-execution-update":
			return;
		case "error":
			return;
	}
}

function setStreamContext(message: RealtimeChatMessage) {
	if (message.type !== "chunk") {
		streamContext.itemId = "";
		streamContext.chunkType = "";
		return;
	}

	const chunk = message.data;

	if (chunk.item_id !== streamContext.itemId) streamContext.itemId = chunk.item_id;
	if (chunk.type !== streamContext.chunkType) streamContext.chunkType = chunk.type;
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

	isLoading.value = true;
	for (const message of await api.chat.load_chat({ chat_id: props.chatId! })) {
		messages.push(message);
	}

	await list_tools.run();
	await updatePendingRequests();
	isLoading.value = false;
	scrollToBottom();
});

onUnmounted(() => socket.off("otto.api.chat", handleRealtimeMessage));

function scrollToBottom() {
	messagesContainer.value?.scrollTo({
		top: messagesContainer.value?.scrollHeight,
	});
}

async function updatePendingRequests() {
	Object.keys(pendingRequests).forEach((key) => delete pendingRequests[key]);
	isLoading.value = true;
	const prs = await api.chat.get_pending_requests({ chat_id: props.chatId! });
	isLoading.value = false;
	for (const pr of prs) pendingRequests[pr.tool_use_id] = pr;
}

async function handleToolExecutionComplete() {
	await updatePendingRequests();
	if (Object.keys(pendingRequests).length > 0) return;
	await handleResume();
}
</script>
<style scoped>
.container-ch {
	--center-width: 768px;
	--lr-spacing: 0px;
}

@media (max-width: 1200px) {
	.container-ch {
		--center-width: 680px;
	}
}

@media (max-width: 992px) {
	.container-ch {
		--center-width: 560px;
	}
}

@media (max-width: 768px) {
	.container-ch {
		--center-width: 100vw;
		--lr-spacing: 2rem;
	}
}

@media (max-width: 480px) {
	.container-ch {
		--center-width: 100vw;
		--lr-spacing: 0.5rem;
	}
}

.chat-messages {
	width: var(--center-width);
	padding: 0 var(--lr-spacing);
}

.chat-input {
	width: var(--center-width);
	padding: 0 var(--lr-spacing);
}
</style>
