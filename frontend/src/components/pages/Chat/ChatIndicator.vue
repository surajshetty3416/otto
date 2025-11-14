<template>
	<div class="px-6 py-1 flex flex-col gap-1 items-center">
		<!-- Loading Indicator-->
		<div class="bg-white/75 backdrop-blur-lg rounded-full p-0.5">
			<LoadingIndicator v-if="isLoading" class="h-3 w-3 text-gray-600 flex-shrink-0" />
			<TextLoadingIndicator v-else-if="save_settings.loading" text="Saving" />
		</div>

		<!-- Labelled Indicator-->
		<div
			v-if="indicatorText"
			class="w-fit px-1 py-0.5 rounded-full flex items-center justify-center gap-1 bg-white/75 backdrop-blur-lg"
		>
			<Lightbulb
				v-if="isThinking"
				class="h-3 w-3 text-gray-600 flex-shrink-0"
				stroke-width="1.5"
			/>
			<Wrench
				v-else-if="isUsingTool"
				class="h-3 w-3 text-gray-600 flex-shrink-0"
				stroke-width="1.5"
			/>
			<LoadingIndicator v-else class="h-3 w-3 text-gray-600 flex-shrink-0" />

			<p class="text-sm text-gray-600">
				<Ellipsis>{{ indicatorText }}</Ellipsis>
			</p>
		</div>

		<!-- Pending requests indicator -->
		<div
			title="Cannot resume chat until all pending requests have been allowed or denied."
			v-if="pendingRequestsCount > 0"
			class="flex items-center justify-between border py-1 px-1 glass-lg w-full -mb-1.5 rounded-md"
			style="border-bottom-left-radius: 0; border-bottom-right-radius: 0"
		>
			<div class="flex items-center gap-2">
				<IndicatorDot color="yellow" class="ml-1.5" />
				<p class="text-sm text-gray-600">
					{{
						pendingRequestsCount > 1
							? `Run ${pendingRequestsCount} pending tools?`
							: "Run pending tool?"
					}}
				</p>
			</div>

			<div class="ml-2 flex items-center gap-1">
				<TextTooltip content="Deny all requests" :keybinds="keybinds['deny-all-requests']">
					<SmallButton
						:loading="acknowledge_request.loading"
						:isPrimary="false"
						@click="denyAll()"
					>
						No
					</SmallButton>
				</TextTooltip>
				<TextTooltip
					content="Grant all requests"
					:keybinds="keybinds['accept-all-requests']"
				>
					<SmallButton
						:loading="acknowledge_request.loading"
						:isPrimary="true"
						@click="grantAll()"
					>
						Yes
					</SmallButton>
				</TextTooltip>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { api } from "@/client";
import type { PendingRequest } from "@/client/generated.types";
import LoadingIndicator from "@/components/fui/LoadingIndicator.vue";
import Ellipsis from "@/components/ui/Ellipsis.vue";
import IndicatorDot from "@/components/ui/IndicatorDot.vue";
import TextTooltip from "@/components/ui/tooltip/TextTooltip.vue";
import shortcuts, { keybinds } from "@/shortcuts";
import { assert } from "@/utils";
import { Lightbulb, Wrench } from "lucide-vue-next";
import { computed, inject, onMounted, onUnmounted } from "vue";
import SmallButton from "./SmallButton.vue";
import { save_settings, streamContextKey, toolConfigKey } from "./utils";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";

const props = defineProps<{
	chatId: string;
	isLoading: boolean;
	isStreaming: boolean;
	isWaitingForStream: boolean;
	pendingRequests: Record<string, PendingRequest>;
}>();

const streamContext = inject(streamContextKey);
const toolConfigs = inject(toolConfigKey);
const pendingRequestsCount = computed(() => Object.keys(props.pendingRequests).length);
const acknowledge_request = api.chat.acknowledge_all_requests(
	{ chat_id: "", status: "Denied" },
	{ auto: false }
);

const first = computed(() => streamContext?.messages.at(0));
const firstContent = computed(() => {
	if (!first.value) return;
	if (first.value?.type !== "chunk" || first.value?.data.type === "system") return;
	return first.value?.data;
});

const isThinking = computed(() => firstContent.value?.type === "thinking");
const isUsingTool = computed(() => firstContent.value?.type === "tool_use");

const toolBeingUsed = computed(() => {
	if (!isUsingTool.value) return;
	assert(firstContent.value?.type === "tool_use", "type check");
	const slug = firstContent.value?.content.name;
	if (!slug) return;
	return toolConfigs?.value[slug]?.title ?? slug;
});

const indicatorText = computed(() => {
	if (isThinking.value) return "Thinking";
	if (isUsingTool.value && toolBeingUsed.value) return `Using the ${toolBeingUsed.value} tool`;
	if (isUsingTool.value && !toolBeingUsed.value) return "Using a tool";
	if (props.isWaitingForStream) return "Waiting for response";
	if (props.isStreaming) return "Responding";
	if (first.value?.type === "request-acknowledge") return "Executing tool";
	if (first.value?.type === "tool-execution-update") return "Processing tool result";
	return;
});

async function grantAll() {
	if (!props.chatId || pendingRequestsCount.value === 0) return;
	await acknowledge_request.run({ chat_id: props.chatId, status: "Granted" }, false);
}

async function denyAll() {
	if (!props.chatId || pendingRequestsCount.value === 0) return;
	await acknowledge_request.run({ chat_id: props.chatId, status: "Denied" }, false);
}

onMounted(() => {
	shortcuts.on("accept-all-requests", grantAll);
	shortcuts.on("deny-all-requests", denyAll);
});
onUnmounted(() => {
	shortcuts.off("accept-all-requests", grantAll);
	shortcuts.off("deny-all-requests", denyAll);
});
</script>
