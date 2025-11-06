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
			<div class="flex flex-col gap-1 p-2">
				<div class="flex items-center gap-2" v-if="chat.assistant_">
					<Bot class="w-3.5 h-3.5 text-gray-600" stroke-width="1.5" />
					<p class="text-xs text-gray-700">{{ chat.assistant_.title }}</p>
				</div>
				<div class="flex items-center gap-2" v-if="chat.model">
					<Sparkle class="w-3.5 h-3.5 text-gray-600" stroke-width="1.5" />
					<p class="text-xs text-gray-700">{{ modelName(chat.model) }}</p>
				</div>
				<div class="flex items-center gap-2">
					<Clock class="w-3.5 h-3.5 text-gray-600" stroke-width="1.5" />
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
import { Bot, Clock, Sparkle } from "lucide-vue-next";
import Tooltip from "../tooltip/Tooltip.vue";
import type { ChatListItem as ChatListItemType } from "./types";
import { computed } from "vue";
const props = defineProps<{ chat: ChatListItemType }>();

function openChat(chatName: string) {
	router.push({ name: "Chat", params: { chatId: chatName } });
}

const isActive = computed(() => {
	return router.currentRoute.value.path.startsWith(`/chat/${props.chat.name}`);
});
</script>
