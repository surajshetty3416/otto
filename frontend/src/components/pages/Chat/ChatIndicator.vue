<template>
	<div class="px-6 py-1 flex flex-col gap-1">
		<!-- Waiting for response indicator -->
		<div v-if="waitingForStream"></div>
		<!-- Pending requests indicator -->
		<div
			title="Cannot resume chat until all pending requests have been allowed or denied."
			v-if="pendingRequestsCount > 0"
			class="flex items-center justify-between border py-1 px-1 bg-gray-50 rounded-sm"
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
import { computed } from "vue";
import SmallButton from "./SmallButton.vue";
import IndicatorDot from "@/components/ui/IndicatorDot.vue";

const props = defineProps<{
	chatId: string;
	isLoading: boolean;
	isStreaming: boolean;
	waitingForStream: boolean;
	pendingRequests: Record<string, PendingRequest>;
}>();

const pendingRequestsCount = computed(() => Object.keys(props.pendingRequests).length);
const acknowledge_request = api.chat.acknowledge_all_requests(
	{ chat_id: "", status: "Denied" },
	{ auto: false }
);
</script>
