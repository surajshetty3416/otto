<template>
	<Tooltip
		class="flex flex-col rounded-md hover:bg-gray-50 cursor-pointer overflow-hidden p-2 -my-2 text-base text-gray-800 w-full text-start text-nowrap"
		:class="{ italic: !chat.title, 'bg-gray-100': isActive }"
		@click="openChat(chat.name)"
		side="right"
		align="start"
	>
		<span class="truncate">
			{{ chat.title ?? "Untitled" }}
		</span>

		<!-- Tooltip content -->
		<template #content>
			<div class="flex flex-col p-2">
				<div class="flex items-center gap-2" v-if="chat.assistant_">
					<p class="text-sm font-medium mb-1 text-gray-900">
						{{ chat.assistant_.title }}
					</p>
				</div>
				<div class="flex items-center gap-2 mb-0.5" v-if="chat.model">
					<Sparkle class="tooltip-icon" stroke-width="1" />
					<p class="text-xs text-gray-700">{{ modelName(chat.model) }}</p>
				</div>
				<div class="flex items-center gap-2">
					<Clock class="tooltip-icon" stroke-width="1" />
					<p class="text-xs text-gray-700">{{ date(chat.modified) }}</p>
				</div>
			</div>
		</template>
	</Tooltip>
</template>

<script setup lang="ts">
import { date } from "@/components/format";
import { modelName } from "@/components/utils";
import router from "@/router";
import { Clock, Sparkle } from "lucide-vue-next";
import { computed } from "vue";
import Tooltip from "../tooltip/Tooltip.vue";
import type { ChatListItem as ChatListItemType } from "./types";
const props = defineProps<{ chat: ChatListItemType }>();

function openChat(chatName: string) {
	router.push({ name: "Chat", params: { chatId: chatName } });
}

const isActive = computed(() => {
	return router.currentRoute.value.path.startsWith(`/chat/${props.chat.name}`);
});
</script>

<style scoped>
.tooltip-icon {
	@apply size-3 text-gray-700;
}
</style>
