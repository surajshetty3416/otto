<template>
	<div class="border-b h-14 w-full p-4 flex items-center justify-between mb-4">
		<h1 class="text-xl font-bold">
			Otto Chat <span class="text-sm font-mono text-gray-500 ml-2">temp header</span>
		</h1>
		<div class="flex items-center gap-3">
			<select
				@change="onChange"
				class="text-sm rounded-md px-2 py-1.5 w-28 border border-gray-300 text-gray-900"
				v-model="selected"
				placeholder="Select a chat"
			>
				<option v-for="chat in list_chats.data" :value="chat.name">
					{{ chat.title || chat.name }}
				</option>
			</select>
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
import { Plus } from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";

const list_chats = api.chat.list_chats(undefined);

const selected = ref<string | null>("");
const props = defineProps<{
	currentChatId?: string;
}>();

function newChat() {
	router.push({ name: "Chat", params: { chatId: "" } });
}

function onChange(event: Event) {
	const target = event.target as HTMLSelectElement;
	const value = target.value;
	if (!value || value === props.currentChatId) return;
	router.push({ name: "Chat", params: { chatId: value } });
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
</script>
