<template>
	<div class="w-screen h-screen flex items-center justify-center flex-col">
		<!-- Header -->
		<ChatHeader :currentChatId="chatId" class="chat-header" />

		<!-- Body -->
		<div class="scroll-container w-full h-screen overflow-y-scroll flex flex-col items-center">
			<!-- Messages -->
			<div
				v-if="messages.length > 0"
				class="border-gray-200 h-full container-ch messages-container"
			>
				<ChatMessages :messages="messages" />
				<div class="chat-spacer-div"></div>
			</div>

			<!-- New chat welcome message -->
			<Welcome v-if="showNew" class="mb-8" style="margin-top: 35vh" />

			<!-- Input -->
			<div
				id="input-container"
				class="w-full container-ch input-container"
				:class="{ 'fixed bottom-0': !showNew }"
			>
				<ChatIndicator
					v-if="chatId"
					:chatId="chatId"
					:isLoading="isLoading"
					:pendingRequests="pendingRequests"
				/>
				<ChatInput
					:chatId="chatId ?? ''"
					:loading="_loading"
					@send="handleSend"
					@settings="openSettings = true"
					v-model="query"
					class="z-20 relative -mx-1"
				/>
				<div
					class="flex flex-row items-center gap-2 pb-4 pt-10 -mt-8 justify-center flex-wrap glass-lg bg-gray-300 -mx-4 z-10 rounded-t-2xl"
				>
					<Selector :canChange="showNew" v-model="assistant" :settings="settings" />
					<TextLoadingIndicator v-if="load_chat.loading" text="Loading settings" />
					<OverrideIndicators v-else v-model="settings" :assistant="assistant" />
				</div>
				<ChatSettingsDialog
					v-model="openSettings"
					v-model:settings="settings"
					:chatId="chatId"
					:isNew="showNew"
					:assistant="assistant"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
/**
 * TODO:
 *
 * - add better error handling
 * - add tasteful animation when popping indicators, collapsing sections
 * - make the streaming of content smoother
 *
 * Error handling:
 * - check if any of the api calls are erroring out, and show an appropriate toast
 * - set a time out on isWaitingForStream, and show a toast (with on click dialog) if it times out
 *
 * - [ ] images and pdfs
 * - [ ] input commands etc `/` and `@` for doctype refs
 * - [ ] tool selection
 *
 * listen in on shortcuts when the page loads, call the functions when they're available
 */
import { api, list_chats } from "@/client";
import {
	type ChatSettings,
	type PendingRequest,
	type RealtimeChatMessage,
	type SessionItem,
	type ToolConfig,
} from "@/client/generated.types";
import { logRealtime } from "@/client/utils";
import { assistants, models } from "@/common";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import { modelName } from "@/components/utils";
import router from "@/router";
import shortcuts from "@/shortcuts";
import socket from "@/socket";
import { assert, isEqual } from "@/utils";
import { useDebounceFn } from "@vueuse/core";
import { computed, nextTick, onMounted, onUnmounted, provide, reactive, ref, watch } from "vue";
import { toast } from "vue-sonner";
import ChatHeader from "./ChatHeader.vue";
import ChatIndicator from "./ChatIndicator.vue";
import ChatInput from "./ChatInput.vue";
import ChatMessages from "./ChatMessages.vue";
import ChatSettingsDialog from "./ChatSettings/ChatSettingsDialog.vue";
import { StreamContext } from "./context";
import OverrideIndicators from "./OverrideIndicators.vue";
import Selector from "./Selector.vue";
import {
	chatState,
	cycleField as cycleFieldvalue,
	getUserSessionItem,
	handleContentChunk,
	handleItem,
	handleToolUseUpdate,
	isReasoningEffort,
	isToolPermission,
	pendingRequestsKey,
	save_settings,
	streamContextKey,
	toolConfigKey,
} from "./utils";
import Welcome from "./Welcome.vue";
import {
	focusInput,
	scrollToTheBottom,
	scrollUserMessageToTheTop,
	setInitialSpacerHeight,
} from "./dom";

const assistant = ref<string>("5t44lus4lh");
const received = new Set<string>(); // sanity check to avoid duplicates
const props = defineProps<{
	chatId?: string;
}>();
const streamContext = new StreamContext();
provide(streamContextKey, streamContext);

const initial: ChatSettings = {
	llm: null,
	reasoning_effort: "Default",
	tool_permissions: "Default",
	user_directives: "",
};
const settings = reactive<ChatSettings>({
	llm: null,
	reasoning_effort: "Default",
	tool_permissions: "Default",
	user_directives: "",
});

// Refs and reactives
const openSettings = ref(false);
const _loading = ref(false); // true if request is being sent
const query = ref<string>(chatState.get(`chat::${props.chatId || "new"}`) ?? "");
const messages = reactive<SessionItem[]>([]);
const pendingRequests = reactive<Record<string, PendingRequest>>({});
const flags = {
	isHandlingNewChatQuery: false,
};

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
provide(pendingRequestsKey, pendingRequests);

async function handleSend() {
	const _query = query.value.trim();
	if (!canSend(_query)) return;

	_loading.value = true;
	await nextTick(); // ensure loading is shown

	if (!props.chatId) {
		const chatId = await api.chat.new_chat({ assistant: assistant.value, settings });
		flags.isHandlingNewChatQuery = true;
		await router.replace({ name: "Chat", params: { chatId } });
		streamContext.set(chatId);
		await nextTick(); // ensure chatId updates post routing
		list_chats.run(undefined, false);
		chatState.delete(`chat::new`);
	}

	assert(props.chatId, "sanity check");
	list_tools.run({ chat_id: props.chatId! }, false);
	appendUserMessage(query.value);
	await api.chat.send_query({ chat_id: props.chatId, query: _query });
	flags.isHandlingNewChatQuery = false;
	query.value = "";
	_loading.value = false;
	streamContext.waiting();
	await nextTick(); // dom state change
}

function canSend(query: string) {
	if (streamContext.isStreamingResponse) {
		toast.info("Model is responding", {
			description: "Please wait for the current response to complete",
		});
		return false;
	}

	if (streamContext.isWaiting) {
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
	nextTick().then(() => scrollUserMessageToTheTop());
}

const scrollToTheBottomDebounced = useDebounceFn(() => scrollToTheBottom(false), 20);
function handleRealtimeMessage(message: RealtimeChatMessage) {
	if (window.is_dev_mode) logRealtime(message);
	streamContext.update(message);

	if (message.type === "error") {
		// make more actionable
		toast.error("Something went wrong", { description: message.data });
	}

	if (message.type === "log" || message.type === "pong") return;
	if (message.chat_id !== props.chatId) return;
	if (received.has(message.id)) return;

	received.add(message.id);
	switch (message.type) {
		case "chunk":
			if (message.data.type === "system")
				// Only used to update stream context
				return;
			else handleContentChunk(message.data, messages);
			scrollToTheBottomDebounced();
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
	}
}

function reset() {
	// Since the component is reused, local state should be reset
	_loading.value = false;
	messages.length = 0;
	received.clear();
	streamContext.reset();
	settings.llm = null;
	settings.reasoning_effort = "Default";
	settings.tool_permissions = "Default";
	settings.user_directives = "";
	Object.keys(pendingRequests).forEach((key) => delete pendingRequests[key]);

	list_tools.reset();
	get_pending_requests.reset();
	load_chat.reset();
}

async function set() {
	setTimeout(focusInput, 100);
	if (!props.chatId) return;
	streamContext.set(props.chatId);
	await list_tools.run({ chat_id: props.chatId }, false);
	await get_pending_requests.run({ chat_id: props.chatId }, false);
	await loadChat();
	nextTick().then(() => {
		console.log(showNew.value);
		setInitialSpacerHeight();
		scrollToTheBottom(true);
	});
}

async function loadChat() {
	assert(props.chatId, "chatId is required"); // type check (caller should ensure)
	const messageIds = messages.map((message) => message.id);
	const chat = await load_chat.run({ chat_id: props.chatId }, false);
	assistant.value = chat.assistant;
	for (const message of chat.messages) {
		if (messageIds.includes(message.id)) continue;
		messages.push(message);
	}

	updateSettings(chat.settings);
}

function updateSettings(source: ChatSettings) {
	initial.llm = source.llm;
	initial.reasoning_effort = source.reasoning_effort ?? "Default";
	initial.tool_permissions = source.tool_permissions ?? "Default";
	initial.user_directives = source.user_directives ?? "";

	settings.llm = initial.llm;
	settings.reasoning_effort = initial.reasoning_effort;
	settings.tool_permissions = initial.tool_permissions;
	settings.user_directives = initial.user_directives;
}

const saveSettings = useDebounceFn(async () => {
	if (!props.chatId || isEqual(initial, settings)) return;
	const _update = await save_settings.run({ chat_id: props.chatId, settings }, false);
	updateSettings(_update);
}, 500);

watch(() => settings, saveSettings, { deep: true });

watch(
	() => query.value,
	() => chatState.set(`chat::${props.chatId || "new"}`, query.value ?? "")
);

onMounted(async () => socket.on("otto.api.chat", handleRealtimeMessage));
onUnmounted(() => socket.off("otto.api.chat", handleRealtimeMessage));

watch(
	() => props.chatId,
	(newVal, oldVal, onCleanup) => {
		if (newVal === oldVal || flags.isHandlingNewChatQuery) return;

		reset();

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

async function handleCycleToolPermissions() {
	if (router.currentRoute.value.name !== "Chat") return;

	const newval = await cycleFieldvalue(settings.tool_permissions, "tool_permissions");
	if (!isToolPermission(newval)) return;

	toast.info("Changing tool permissions to " + newval);
	settings.tool_permissions = newval;
}

async function handleCycleReasoningEffort() {
	if (router.currentRoute.value.name !== "Chat") return;

	const ast = assistants.value[assistant.value];
	const llm = models.value[ast.llm];
	if (!llm.is_reasoning) {
		toast.info(`${modelName(llm)} does not support reasoning`);
		return;
	}

	let newval = await cycleFieldvalue(settings.reasoning_effort, "reasoning_effort");
	if (!isReasoningEffort(newval) && newval !== "Default") return;

	toast.info("Changing reasoning effort to " + newval);
	settings.reasoning_effort = newval;
}

onMounted(() => {
	shortcuts.on("cycle-tool-permissions", handleCycleToolPermissions);
	shortcuts.on("cycle-reasoning-effort", handleCycleReasoningEffort);
});

onUnmounted(() => {
	shortcuts.off("cycle-tool-permissions", handleCycleToolPermissions);
	shortcuts.off("cycle-reasoning-effort", handleCycleReasoningEffort);
});
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

.messages-container {
	width: var(--center-width);
	padding: 0 var(--lr-spacing);
}

.input-container {
	width: var(--center-width);
	padding: 0 var(--lr-spacing);
}
</style>
