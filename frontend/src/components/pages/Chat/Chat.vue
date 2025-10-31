<template>
	<div class="w-screen h-screen flex items-center justify-center flex-col">
		<!-- Header -->
		<ChatHeader :currentChatId="chatId" />

		<!-- Body -->
		<div
			class="w-full h-full overflow-y-scroll flex flex-col items-center"
			ref="messagesContainer"
		>
			<!-- Messages -->
			<div
				v-if="messages.length > 0"
				class="border-gray-200 h-full container-ch chat-messages"
			>
				<ChatMessages :messages="messages" />
				<div style="height: 20vh; flex-shrink: 0"></div>
			</div>

			<!-- New chat welcome message -->
			<div v-if="showNew" class="mb-8" style="margin-top: 35vh">
				<p class="text-gray-800 text-4xl font-medium">What can I help you with?</p>
			</div>

			<!-- Input -->
			<div class="w-full container-ch chat-input" :class="{ 'fixed bottom-8': !showNew }">
				<ChatIndicator
					v-if="chatId"
					:chatId="chatId"
					:isLoading="isLoading"
					:isStreaming="isStreaming"
					:isWaitingForStream="isWaitingForStream"
					:pendingRequests="pendingRequests"
				/>
				<ChatInput :loading="_loading" @send="handleSend" />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
/**
 * TODO:
 * - add tasteful animation when popping indicators, collapsing sections
 * - add better error handling
 * - make the streaming of content smoother
 */
import { api } from "@/client";
import type {
	PendingRequest,
	RealtimeChatMessage,
	SessionItem,
	TextContentChunk,
	ToolConfig,
} from "@/client/generated.types";
import router from "@/router";
import socket from "@/socket";
import { assert, sleep } from "@/utils";
import { computed, onMounted, onUnmounted, provide, reactive, ref, watch } from "vue";
import { toast } from "vue-sonner";
import ChatHeader from "./ChatHeader.vue";
import ChatIndicator from "./ChatIndicator.vue";
import ChatInput from "./ChatInput.vue";
import ChatMessages from "./ChatMessages.vue";
import type { StreamContext } from "./types";
import {
	getToolUseContent,
	getUserSessionItem,
	handleContentChunk,
	handleItem,
	handleToolUseUpdate,
	pendingRequestsKey,
	streamContextKey,
	toolConfigKey,
	updateStreamContext,
} from "./utils";

/**
 * When streaming show a spinner above the input about what is going on, e.g.
 * thinking, calling tool, responding, waiting for permission, etc.
 *
 * when showing a list of item pills (thought, tool calls, etc) on clicking open
 * the dialog below and highlight that the item is open.
 */

// const assistant = "1rv777j9m3"; // Sonnet 4.5 with reasoning
const assistant = "5t44lus4lh"; // Haiku
const received = new Set<string>(); // sanity check to avoid duplicates
const props = defineProps<{
	chatId?: string;
}>();

// Refs and reactives
const _loading = ref(false); // true if request is being sent
const isStreaming = ref(false); // true if chat is streaming
const isWaitingForStream = ref(false); // true if waiting for stream to start
const messagesContainer = ref<HTMLDivElement | null>(null);
const messages = reactive<SessionItem[]>([]);
const streamContext = reactive<StreamContext>({ messages: [], isStreamingResponse: false });
const pendingRequests = reactive<Record<string, PendingRequest>>({});

// API calls
const list_tools = api.chat.list_tools({ chat_id: "" }, { auto: false });
const get_pending_requests = api.chat.get_pending_requests({ chat_id: "" }, { auto: false });
const resume_chat = api.chat.resume_chat({ chat_id: "" }, { auto: false });
const load_chat = api.chat.load_chat({ chat_id: "" }, { auto: false });

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
const hasPendingToolExecutions = computed(() => {
	for (let i = messages.length - 1; i >= 0; i--) {
		const message = messages[i];
		for (const content of message.content) {
			if (content.type !== "tool_use") continue;
			if (content.status === "pending") return true;
		}
	}
	return false;
});
const showNew = computed(() => {
	if (load_chat.loading) return false;
	if (messages.length > 0) return false;
	if (props.chatId) return false;
	if (!load_chat.loading && messages.length === 0 && props.chatId) return true;
	return true;
});

provide(toolConfigKey, toolConfigs);
provide(streamContextKey, streamContext);
provide(pendingRequestsKey, pendingRequests);

async function handleSend(query: string) {
	if (!canSend(query)) return;

	_loading.value = true;
	if (!props.chatId) {
		const chatId = await api.chat.new_chat({ assistant });
		await router.replace({ name: "Chat", params: { chatId } });
		await updatePendingRequests();
	}
	appendUserMessage(query);

	assert(props.chatId, "chatId is required");
	await api.chat.send_query({ chat_id: props.chatId, query });
	_loading.value = false;
	isWaitingForStream.value = true;
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

	if (isWaitingForStream.value) {
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

	if (hasPendingToolExecutions.value) {
		toast.warning("Tool execution pending", {
			description: "Please wait until pending tools have completed running",
		});
		return false;
	}
	return true;
}

async function handleResume() {
	await resume_chat.run({ chat_id: props.chatId! }, false);
	isWaitingForStream.value = true;
}

function appendUserMessage(query: string) {
	messages.push(getUserSessionItem(query));
}

function handleRealtimeMessage(message: RealtimeChatMessage) {
	if (window.is_dev_mode) console.log(message);

	isWaitingForStream.value = false;
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
			handleRequest(message.data);
			return;
		case "tool-execution-update":
			handleToolUseUpdate(message.data, messages);
			return;
		case "tool-execution-complete":
			updateRequestsAndResume();
			return;
		case "request-acknowledge":
			updateRequestsAndResume(message.data);
			return;
		case "error":
			toast.error("Error in chat", {
				description: message.data,
			});
			return;
	}
}

function handleRequest(pr: PendingRequest) {
	pendingRequests[pr.tool_use_id] = pr;
	const tool = getToolUseContent(pr.tool_use_id, messages);
	if (!tool) return;

	const config = toolConfigs.value[tool.name];
	if (!config) return;

	toast.info("Permission request", {
		description: `Requested to run ${config.title}`,
	});
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

function scrollToBottom() {
	messagesContainer.value?.scrollTo({
		top: messagesContainer.value?.scrollHeight,
		behavior: "smooth",
	});
}

async function updateRequestsAndResume(toolUseIds?: string[]) {
	await updatePendingRequests(toolUseIds);
	if (Object.keys(pendingRequests).length > 0) return;
	await handleResume();
}

async function updatePendingRequests(toolUseIds?: string[], clearAll: boolean = false) {
	if (!toolUseIds) {
		toolUseIds = clearAll ? Object.keys(pendingRequests) : [];
	}

	for (const toolUseId of toolUseIds) {
		delete pendingRequests[toolUseId];
	}

	if (!props.chatId) return;
	const prs = await get_pending_requests.run({ chat_id: props.chatId! }, false);
	for (const pr of prs) pendingRequests[pr.tool_use_id] = pr;
}

onMounted(async () => {
	socket.on("otto.api.chat", handleRealtimeMessage);
	await set();
});

onUnmounted(() => {
	socket.off("otto.api.chat", handleRealtimeMessage);
	clear(); // no-op
});

function clear() {
	// Since the component is reused, local state should be reset
	_loading.value = false;
	isStreaming.value = false;
	isWaitingForStream.value = false;
	messages.length = 0;
	streamContext.messages.length = 0;
	streamContext.isStreamingResponse = false;
	Object.keys(pendingRequests).forEach((key) => delete pendingRequests[key]);

	list_tools.reset();
	get_pending_requests.reset();
	resume_chat.reset();
	load_chat.reset();
}

async function set() {
	if (!props.chatId) return;
	await list_tools.run({ chat_id: props.chatId }, false);
	await updatePendingRequests();
	await loadChat();
}

async function loadChat() {
	assert(props.chatId, "chatId is required"); // type check (caller should ensure)
	const messageIds = messages.map((message) => message.id);
	for (const message of await load_chat.run({ chat_id: props.chatId }, false)) {
		if (messageIds.includes(message.id)) continue;
		messages.push(message);
	}

	sleep(10).then(() => scrollToBottom());
}

watch(
	() => props.chatId,
	(newVal, oldVal, onCleanup) => {
		if (newVal === oldVal) return;

		// cancel requests called in `set` if id change
		const controller = new AbortController();
		list_tools.signal = controller.signal;
		get_pending_requests.signal = controller.signal;
		load_chat.signal = controller.signal;
		onCleanup(() => controller.abort());

		clear();
		set();
	},
	{ immediate: true, flush: "sync" }
);
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
