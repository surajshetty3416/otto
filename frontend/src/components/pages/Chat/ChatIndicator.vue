<template>
	<div class="px-6 py-1 flex flex-col gap-1 items-center">
		<!-- Loading Indicator-->
		<div class="bg-white/75 backdrop-blur-lg rounded-full p-0.5">
			<LoadingIndicator v-if="isLoading" class="h-3 w-3 text-gray-600 flex-shrink-0" />
		</div>

		<!-- Labelled Indicator-->
		<div
			v-if="indicatorText"
			class="w-fit px-1 py-0.5 rounded-full flex items-center justify-center gap-1 bg-white/75 backdrop-blur-lg"
		>
			<Brain
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
			class="flex items-center justify-between border py-1 px-1 bg-gray-50/80 backdrop-blur-md rounded-sm w-full"
		>
			<div class="flex items-center gap-2">
				<IndicatorDot color="yellow" class="ml-1.5" />
				<p class="text-sm text-gray-600">
					{{
						pendingRequestsCount > 1
							? `Allow running ${pendingRequestsCount} pending tools?`
							: "Allow running pending tool?"
					}}
				</p>
			</div>

			<div class="ml-2 flex items-center gap-1">
				<SmallButton
					:loading="acknowledge_request.loading"
					@click="acknowledge_request.run({ chat_id: props.chatId, status: 'Denied' })"
					>No</SmallButton
				>
				<SmallButton
					:loading="acknowledge_request.loading"
					:isPrimary="true"
					@click="acknowledge_request.run({ chat_id: props.chatId, status: 'Granted' })"
					>Yes</SmallButton
				>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { api } from "@/client";
import type { PendingRequest } from "@/client/generated.types";
import IndicatorDot from "@/components/ui/IndicatorDot.vue";
import { assert } from "@/utils";
import { Brain, Wrench } from "lucide-vue-next";
import { computed, inject } from "vue";
import Ellipsis from "./Ellipsis.vue";
import SmallButton from "./SmallButton.vue";
import { streamContextKey, toolConfigKey } from "./utils";
import LoadingIndicator from "@/components/fui/LoadingIndicator.vue";

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

const first = computed(() => {
	const first = streamContext?.messages.at(0);
	if (!first) return;
	if (first.type !== "chunk" || first.data.type === "system") return;
	return first.data;
});

const isThinking = computed(() => first.value?.type === "thinking");
const isUsingTool = computed(() => first.value?.type === "tool_use");

const toolBeingUsed = computed(() => {
	if (!isUsingTool.value) return;
	assert(first.value?.type === "tool_use", "type check");
	const slug = first.value?.content.name;
	if (!slug) return;
	return toolConfigs?.value[slug]?.title ?? slug;
});

const indicatorText = computed(() => {
	if (isThinking.value) return "Thinking";
	if (isUsingTool.value && toolBeingUsed.value) return `Using the ${toolBeingUsed.value} tool`;
	if (isUsingTool.value && !toolBeingUsed.value) return "Using a tool";
	if (props.isWaitingForStream) return "Waiting for response";
	if (props.isStreaming) return "Responding";
	return;
});
</script>
