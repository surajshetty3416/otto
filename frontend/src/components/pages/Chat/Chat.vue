<template>
	<div class="w-screen h-screen flex items-center justify-center flex-col">
		<!-- Header -->
		<ChatHeader :currentChatId="chatId" />

		<!-- Body -->
		<div
			class="w-full h-screen overflow-y-scroll flex flex-col items-center pt16"
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
			<Welcome v-if="showNew" class="mb-8" style="margin-top: 35vh" />

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
				<ChatInput
					:chatId="chatId ?? ''"
					:loading="_loading"
					@send="handleSend"
					@settings="openSettings = true"
					v-model="query"
				/>
				<Selector class="mt-2" v-if="showNew" v-model="assistant" />
				<ChatSettingsDialog v-model="openSettings" :chatId="chatId" :isNew="showNew" />
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
 *
 * Error handling:
 * - check if any of the api calls are erroring out, and show an appropriate toast
 * - set a time out on isWaitingForStream, and show a toast if it times out
 *
 * - [ ] sidebar (select chat, nav to assistants, tools, etc)
 * - [ ] allow assistant config llm, tools, etc (default?)
 * - [ ] images and pdfs
 * - [ ] input commands etc `/` and `@` for doctype refs
 */
import { api, list_chats } from "@/client";
import type {
	PendingRequest,
	RealtimeChatMessage,
	SessionItem,
	TextContentChunk,
	ToolConfig,
} from "@/client/generated.types";
import { logRealtime } from "@/client/utils";
import router from "@/router";
import socket from "@/socket";
import { assert } from "@/utils";
import { computed, nextTick, onMounted, onUnmounted, provide, reactive, ref, watch } from "vue";
import { toast } from "vue-sonner";
import ChatHeader from "./ChatHeader.vue";
import ChatIndicator from "./ChatIndicator.vue";
import ChatInput from "./ChatInput.vue";
import ChatMessages from "./ChatMessages.vue";
import ChatSettingsDialog from "./ChatSettings/ChatSettingsDialog.vue";
import Selector from "./Selector.vue";
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
import Welcome from "./Welcome.vue";

const openSettings = ref(true);
const assistant = ref<string>("5t44lus4lh");
const received = new Set<string>(); // sanity check to avoid duplicates
const props = defineProps<{
	chatId?: string;
}>();

// Refs and reactives
const _loading = ref(false); // true if request is being sent
const query = ref("");
const isStreaming = ref(false); // true if chat is streaming
const isWaitingForStream = ref(false); // true if waiting for stream to start
const messagesContainer = ref<HTMLDivElement | null>(null);
const messages = reactive<SessionItem[]>([]);
const streamContext = reactive<StreamContext>({ messages: [], isStreamingResponse: false });
const pendingRequests = reactive<Record<string, PendingRequest>>({});

// API calls
const list_tools = api.chat.list_tools({ chat_id: "" }, { auto: false });
const get_pending_requests = api.chat.get_pending_requests({ chat_id: "" }, { auto: false });
const load_chat = api.chat.load_chat({ chat_id: "" }, { auto: false });

const isLoading = computed(
	() => list_tools.loading || load_chat.loading || get_pending_requests.loading || _loading.value
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

	// For when there's a non-new chat that is empty, show the welcome message
	if (!load_chat.loading && messages.length === 0 && props.chatId) return true;

	return true;
});

provide(toolConfigKey, toolConfigs);
provide(streamContextKey, streamContext);
provide(pendingRequestsKey, pendingRequests);

async function handleSend() {
	const _query = query.value.trim();
	if (!canSend(_query)) return;

	_loading.value = true;
	await nextTick(); // ensure loading is shown

	if (!props.chatId) {
		const chatId = await api.chat.new_chat({ assistant: assistant.value });
		await router.replace({ name: "Chat", params: { chatId } });
		await nextTick(); // ensure chatId updates post routing
		list_chats.run(undefined, false);
	}

	assert(props.chatId, "sanity check");
	appendUserMessage(query.value);
	await api.chat.send_query({ chat_id: props.chatId, query: _query });
	query.value = "";
	_loading.value = false;
	isWaitingForStream.value = true;
	await nextTick(); // dom state change
	await list_tools.run({ chat_id: props.chatId! }, false);
}

function canSend(query: string) {
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

	if (!query) {
		toast.warning("Empty message", {
			description: "Please enter a message before sending",
		});
		return false;
	}
	return true;
}

function appendUserMessage(query: string) {
	messages.push(getUserSessionItem(query));
}

function handleRealtimeMessage(message: RealtimeChatMessage) {
	if (window.is_dev_mode) logRealtime(message);

	isWaitingForStream.value = false;
	updateStreamContext(message, streamContext);

	if (message.chat_id !== props.chatId) return;
	if (received.has(message.id)) return;

	received.add(message.id);
	switch (message.type) {
		case "chunk":
			if (message.data.type === "system") handleSystemChunk(message.data);
			else handleContentChunk(message.data, messages);
			scrollToBottom("instant");
			return;
		case "item":
			handleItem(message.data, messages);
			return;
		case "request":
			pendingRequests[message.data.tool_use_id] = message.data;
			return;
		case "tool-execution-update":
			handleToolUseUpdate(message.data, messages);
			return;
		case "request-acknowledge":
			message.data.forEach((toolUseId) => delete pendingRequests[toolUseId]);
			return;
		case "title-update":
			list_chats.run(undefined, false);
			return;
		case "error":
			toast.error("Error in chat", { description: message.data });
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

function scrollToBottom(behavior: "smooth" | "instant") {
	messagesContainer.value?.scrollTo({
		top: messagesContainer.value?.scrollHeight,
		behavior,
	});
}

function clear() {
	// Since the component is reused, local state should be reset
	_loading.value = false;
	isStreaming.value = false;
	isWaitingForStream.value = false;
	messages.length = 0;
	streamContext.messages.length = 0;
	streamContext.isStreamingResponse = false;
	received.clear();
	Object.keys(pendingRequests).forEach((key) => delete pendingRequests[key]);

	list_tools.reset();
	get_pending_requests.reset();
	load_chat.reset();
}

async function set() {
	setTimeout(focus, 100);
	if (!props.chatId) return;
	await list_tools.run({ chat_id: props.chatId }, false);
	await get_pending_requests.run({ chat_id: props.chatId }, false);
	await loadChat();
}

function focus() {
	const input = document.getElementById(`chat-input`);
	if (!input || !(input instanceof HTMLInputElement) || input.disabled || input.readOnly) return;
	input.focus();
}

async function loadChat() {
	assert(props.chatId, "chatId is required"); // type check (caller should ensure)
	const messageIds = messages.map((message) => message.id);
	for (const message of await load_chat.run({ chat_id: props.chatId }, false)) {
		if (messageIds.includes(message.id)) continue;
		messages.push(message);
	}

	nextTick().then(() => scrollToBottom("smooth"));
}

onMounted(async () => socket.on("otto.api.chat", handleRealtimeMessage));
onUnmounted(() => socket.off("otto.api.chat", handleRealtimeMessage));

watch(
	() => props.chatId,
	(newVal, oldVal, onCleanup) => {
		if (newVal === oldVal) return;

		clear();

		// cancel requests called in `set` if id change
		const controller = new AbortController();
		list_tools.signal = controller.signal;
		get_pending_requests.signal = controller.signal;
		load_chat.signal = controller.signal;
		onCleanup(() => controller.abort());

		set();
	},
	{ immediate: true, flush: "sync" }
);

watch(
	() => get_pending_requests.data,
	(newVal) => {
		if (!newVal) return; // new value empty on clear, it will be set again
		Object.keys(pendingRequests).forEach((key) => delete pendingRequests[key]);
		for (const pr of newVal) {
			pendingRequests[pr.tool_use_id] = pr;
		}
	},
	{ immediate: true }
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
