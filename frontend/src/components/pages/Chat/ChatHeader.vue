<template>
	<div class="border-b h-14 w-full p-4 flex items-center justify-between mb-4">
		<h1 class="text-xl font-bold">
			Otto Chat
			<span class="text-sm font-mono text-gray-500 font-semibold ml-2">temp header</span>
		</h1>
		<div class="flex items-center gap-3">
			<Button
				:loading="delete_chat.loading"
				variant="subtle"
				@click="deleteChat"
				v-if="currentChatId"
			>
				<Trash class="w-4 h-4" />
			</Button>
			<Button variant="subtle" @click="newChat">
				<template #prefix>
					<Plus class="w-4 h-4" />
				</template>
				New</Button
			>
		</div>
	</div>
</template>
<script setup lang="ts">
import { api } from "@/client";
import Button from "@/components/fui/Button/Button.vue";
import router from "@/router";
import { Plus, Trash } from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";

const delete_chat = api.chat.delete_chat({ chat_id: "" }, { auto: false });
const list_chats = api.chat.list_chats(undefined);

async function deleteChat() {
	await delete_chat.run({ chat_id: props.currentChatId! }, false);
	await list_chats.run(undefined, false);
	newChat();
}

const selected = ref<string>("");
const props = defineProps<{
	currentChatId?: string;
}>();

function newChat() {
	router.push({ name: "Chat", params: { chatId: "" } });
}

const names = computed(() => {
	return list_chats.data?.map((c) => String(c.name)) ?? [];
});

watch(
	() => props.currentChatId,
	(newVal) => {
		selected.value = newVal ?? "";
		if (newVal && !names.value.includes(newVal)) list_chats.run(undefined, false);
	}
);

onMounted(() => {
	selected.value = props.currentChatId ?? "";
});

const chatOptions = computed(() => {
	const options =
		list_chats.data?.map((c) => ({ label: c.title || c.name, value: c.name })) ?? [];
	if (!props.currentChatId) {
		options.unshift({ label: "New Chat", value: "" });
	}
	return options;
});
</script>
