<template>
	<div class="flex flex-col transition-all duration-200">
		<!-- Header -->
		<button
			class="flex items-center justify-between px-2 cursor-pointer"
			@click="isOpen = !isOpen"
		>
			<p class="text-sm font-medium text-gray-600">Chats</p>
			<ChevronDown
				class="w-4 h-4 text-gray-600 transition-transform duration-300"
				:class="{ 'rotate-90': !isOpen }"
				stroke-width="1.5"
			/>
		</button>

		<TextLoadingIndicator v-if="list_chats.loading" class="p-2" text="Loading chats" />

		<!-- List -->
		<Transition
			enter-active-class="transition-all duration-150 ease-out"
			leave-active-class="transition-all duration-150 ease-in"
			enter-from-class="opacity-0 max-h-0"
			enter-to-class="opacity-100 max-h-[1000px]"
			leave-from-class="opacity-100 max-h-[1000px]"
			leave-to-class="opacity-0 max-h-0"
		>
			<div v-if="list_chats.data && isOpen" class="mt-2 h-full overflow-hidden">
				<template v-for="chat in chats" :key="chat.name">
					<ChatListItem :chat="chat" />
				</template>

				<p
					v-if="chats.length === 0 && !list_chats.loading"
					class="p-2 text-sm text-gray-600"
				>
					No chats yet
				</p>
			</div>
		</Transition>
	</div>
</template>

<script setup lang="ts">
import { list_chats } from "@/client";
import { assistants, models } from "@/common";
import { ChevronDown } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import TextLoadingIndicator from "../TextLoadingIndicator.vue";
import ChatListItem from "./ChatListItem.vue";
import type { ChatListItem as ChatListItemType } from "./types";
import { sidebarState } from "./utils";

const isOpen = ref(sidebarState.get("isChatListOpen") ?? true);
watch(isOpen, (value) => sidebarState.set("isChatListOpen", value));
const chats = computed(() => {
	if (!list_chats.data) return [];

	const chats: ChatListItemType[] = [];
	for (const chat of list_chats.data) {
		const assistant_ = assistants.value[chat.assistant];
		const model = models.value[assistant_?.llm];
		chats.push({ ...chat, assistant_, model });
	}

	return chats;
});
</script>
