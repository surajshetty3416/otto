<template>
	<Header class="px-4 flex items-center justify-between">
		<Button title="Start a new chat" variant="subtle" @click="newChat" v-if="currentChatId">
			<template #prefix>
				<Plus class="w-4 h-4 text-gray-600" stroke-width="1.5" />
			</template>
			New
		</Button>
		<Button
			title="Delete this chat"
			:loading="delete_chat.loading"
			variant="ghost"
			@click="deleteChat"
			v-if="currentChatId"
		>
			<Trash class="w-4 h-4 text-gray-600" />
		</Button>
	</Header>
</template>
<script setup lang="ts">
import { api } from "@/client";
import Button from "@/components/fui/Button/Button.vue";
import Header from "@/components/ui/Header.vue";
import router from "@/router";
import { Plus, Trash } from "lucide-vue-next";
import { computed, ref, watch } from "vue";

const delete_chat = api.chat.delete_chat({ chat_id: "" }, { auto: false });
const list_chats = api.chat.list_chats();

async function deleteChat() {
	await delete_chat.run({ chat_id: props.currentChatId! }, false);
	await list_chats.run(null, false);
	newChat();
}

const selected = ref<string>("");
const props = defineProps<{
	currentChatId?: string;
}>();

function newChat() {
	router.push({ name: "Chat", params: { chatId: "" } });
}

const names = computed(() => list_chats.data?.map((c) => String(c.name)) ?? []);

watch(
	() => props.currentChatId,
	(newVal) => {
		selected.value = newVal ?? "";
		if (newVal && !names.value.includes(newVal)) list_chats.run(null, false);
	}
);
</script>
