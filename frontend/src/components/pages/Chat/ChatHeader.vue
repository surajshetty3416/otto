<template>
	<Header class="px-4 flex items-center justify-between">
		<TextTooltip content="Start a new chat" :keybinds="keybinds['new-chat']" :delay="250">
			<Button variant="subtle" @click="newChat" v-if="currentChatId">
				<template #prefix>
					<Plus class="w-4 h-4 text-gray-600" stroke-width="1.5" />
				</template>
				New
			</Button>
		</TextTooltip>
		<TextTooltip content="Delete this chat" :keybinds="keybinds['delete-chat']" :delay="250">
			<Button
				:loading="delete_chat.loading"
				variant="ghost"
				@click="showDelete"
				v-if="currentChatId"
			>
				<Trash class="w-4 h-4 text-gray-600" />
			</Button>
		</TextTooltip>

		<Dialog :open="openDelete" @update:open="openDelete = $event">
			<DialogContent>
				<template #header>
					<DialogTitle class="flex items-center gap-2">
						<TriangleAlert class="w-4 h-4 text-red-500" stroke-width="1.5" />
						Delete Chat</DialogTitle
					>
				</template>

				<p class="text-base text-gray-900">
					This will delete <span class="font-semibold">"{{ title }}"</span>
				</p>

				<p class="text-base text-gray-900">
					Are you sure you want to delete this chat? This action cannot be undone.
				</p>

				<template #buttons>
					<Button variant="outline" size="md" @click="openDelete = false">Cancel</Button>
					<Button variant="solid" size="md" @click="deleteChat" autofocus>Delete</Button>
				</template>
			</DialogContent>
		</Dialog>
	</Header>
</template>
<script setup lang="ts">
import { api, list_chats } from "@/client";
import Button from "@/components/fui/Button/Button.vue";
import Dialog from "@/components/ui/dialog/Dialog.vue";
import DialogContent from "@/components/ui/dialog/DialogContent.vue";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import Header from "@/components/ui/Header.vue";
import TextTooltip from "@/components/ui/tooltip/TextTooltip.vue";
import router from "@/router";
import shortcuts, { keybinds } from "@/shortcuts";
import { Plus, Trash, TriangleAlert } from "lucide-vue-next";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

const delete_chat = api.chat.delete_chat({ chat_id: "" }, { auto: false });
const openDelete = ref(false);

async function showDelete(e?: KeyboardEvent | MouseEvent) {
	e?.preventDefault();
	e?.stopPropagation();
	if (!props.currentChatId) return;
	openDelete.value = true;
}

async function deleteChat() {
	openDelete.value = false;
	newChat();
	await delete_chat.run({ chat_id: props.currentChatId! }, false);
	await list_chats.run(null, false);
}

const selected = ref<string>("");
const props = defineProps<{
	currentChatId?: string;
}>();

function newChat() {
	router.push({ name: "Chat", params: { chatId: "" } });
}

const names = computed(() => list_chats.data?.map((c) => String(c.name)) ?? []);
const title = computed(() => {
	if (!props.currentChatId) return "";
	const chat = list_chats.data?.find((c) => c.name === props.currentChatId);
	return chat?.title ?? chat?.name ?? "";
});

watch(
	() => props.currentChatId,
	(newVal) => {
		selected.value = newVal ?? "";
		if (newVal && !names.value.includes(newVal)) list_chats.run(null, false);
	}
);

onMounted(() => {
	shortcuts.on("delete-chat", showDelete);
});
onUnmounted(() => {
	shortcuts.off("delete-chat", showDelete);
});
</script>
