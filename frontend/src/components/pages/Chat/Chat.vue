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
			<div class="fixed bottom-8 w-full container-ch chat-input">
				<ChatIndicator
					v-if="chatId"
					:chatId="chatId"
					:isLoading="isLoading"
					:isStreaming="isStreaming"
					:waitingForStream="waitingForStream"
					:pendingRequests="pendingRequests"
				/>
				<ChatInput :loading="_loading" @send="handleSend" />
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
import ChatIndicator from "./ChatIndicator.vue";
import ChatInput from "./ChatInput.vue";
import ChatMessages from "./ChatMessages.vue";
import type { StreamContext } from "./types";
import {
	getUserSessionItem,
	handleContentChunk,
	handleItem,
	handleToolUseUpdate,
	pendingRequestsKey,
	streamContextKey,
	toolConfigKey,
	updateStreamContext,
} from "./utils";
import { toast } from "vue-sonner";

/**
 * When streaming show a spinner above the input about what is going on, e.g.
 * thinking, calling tool, responding, waiting for permission, etc.
 *
 * when showing a list of item pills (thought, tool calls, etc) on clicking open
 * the dialog below and highlight that the item is open.
 */

const assistant = "1rv777j9m3"; // dummy for now
const received = new Set<string>(); // sanity check to avoid duplicates
const props = defineProps<{
	chatId?: string;
}>();

const _loading = ref(false); // true if request is being sent
const isStreaming = ref(false); // true if chat is streaming
const waitingForStream = ref(false); // true if waiting for stream to start
const messagesContainer = ref<HTMLDivElement | null>(null);
const messages = reactive<SessionItem[]>([]);
const streamContext = reactive<StreamContext>({ chunks: [], isStreamingResponse: false });
const pendingRequests = reactive<Record<string, PendingRequest>>({});

// API calls
const list_tools = api.chat.list_tools({ chat_id: "" }, { auto: false });
const get_pending_requests = api.chat.get_pending_requests({ chat_id: "" }, { auto: false });
const resume_chat = api.chat.resume_chat({ chat_id: "" }, { auto: false });
const load_chat = api.chat.load_chat({ chat_id: "" }, { auto: false });

const isNew = computed(() => !props.chatId);
const isLoading = computed(
	() =>
		resume_chat.loading ||
		list_tools.loading ||
		load_chat.loading ||
		get_pending_requests.loading ||
		_loading.value
);
const toolConfigs = computed(() => {
	const configs: Record<string, ToolConfig> = {};
	for (const tool of list_tools.data ?? []) {
		configs[tool.slug] = tool;
	}
	return configs;
});

provide(toolConfigKey, toolConfigs);
provide(streamContextKey, streamContext);
provide(pendingRequestsKey, pendingRequests);

async function handleSend(query: string) {
	if (!canSend(query)) return;

	_loading.value = true;
	if (isNew.value) {
		const chatId = await api.chat.new_chat({ assistant });
		await router.replace({ name: "Chat", params: { chatId } });
		await updatePendingRequests();
	}
	appendUserMessage(query);

	assert(props.chatId, "chatId is required");
	await api.chat.send_query({ chat_id: props.chatId, query });
	_loading.value = false;
	waitingForStream.value = true;
	await list_tools.run({ chat_id: props.chatId! }, false);
}

function canSend(query: string) {
	if (resume_chat.loading) {
		toast.info("Resuming chat", {
			description: "Please wait a response is in progress",
		});
		return false;
	}

	if (isStreaming.value) {
		toast.info("Model is responding", {
			description: "Please wait for the current response to complete",
		});
		return false;
	}

	if (waitingForStream.value) {
		toast.info("Waiting for response", {
			description: "Please wait for the current response to complete",
		});
		return false;
	}

	if (!query.trim()) {
		toast.warning("Empty message", {
			description: "Please enter a message to send",
		});
		return false;
	}

	if (Object.keys(pendingRequests).length > 0) {
		toast.warning("Request pending", {
			description: "Please acknowledge all pending requests",
		});

		return false;
	}
	return true;
}

async function handleResume() {
	await resume_chat.run({ chat_id: props.chatId! }, false);
	waitingForStream.value = true;
}

function appendUserMessage(query: string) {
	messages.push(getUserSessionItem(query));
}

function handleRealtimeMessage(message: RealtimeChatMessage) {
	if (window.is_dev_mode) console.log(message);

	waitingForStream.value = false;
	updateStreamContext(message, streamContext);

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
			handleToolUseUpdate(message.data, messages);
			return;
		case "request-acknowledge":
			updatePendingRequests(message.data);
			return;
		case "error":
			// TODO: need better error handling
			toast.error("Error in chat", {
				description: message.data,
			});
			return;
	}
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

	for (const message of await load_chat.run({ chat_id: props.chatId! }, false)) {
		messages.push(message);
	}

	await list_tools.run({ chat_id: props.chatId! });
	await updatePendingRequests();
	scrollToBottom();
});

onUnmounted(() => socket.off("otto.api.chat", handleRealtimeMessage));

function scrollToBottom() {
	messagesContainer.value?.scrollTo({
		top: messagesContainer.value?.scrollHeight,
	});
}

async function updatePendingRequests(toolUseIds?: string[]) {
	if (!toolUseIds) {
		toolUseIds = Object.keys(pendingRequests);
	}

	for (const toolUseId of toolUseIds) {
		delete pendingRequests[toolUseId];
	}
	const prs = await get_pending_requests.run({ chat_id: props.chatId! }, false);
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
