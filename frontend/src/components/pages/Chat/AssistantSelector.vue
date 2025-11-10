<template>
	<Popover v-model:open="isOpen">
		<PopoverTrigger
			title="Select an assistant"
			class="flex gap-1 items-center justify-center rounded-lg px-2 py-1"
			:class="{ 'ring-1 ring-gray-200': isOpen }"
		>
			<component :is="icon" class="w-3.5 h-3.5 shrink-0 text-gray-700" stroke-width="1.5" />
			<span class="text-nowrap text-sm text-gray-800">
				{{ assistants[selected.assistant]?.title }}
			</span>
		</PopoverTrigger>

		<PopoverContent class="p-0 rounded-lg border border-gray-200 shadow-sm w-60 min-w-fit">
			<template v-for="assistant in assistants_list" :key="assistant.name">
				<SelectorAssistantItem
					@click="select(assistant)"
					:assistant="assistant"
					:selected="selected"
					:active="false"
				/>
			</template>

			<hr class="border-gray-100" />
			<SelectorItem
				@click="more"
				title="More"
				:icon="List"
				description="View all assistants"
			/>
			<SelectorItem
				@click="customize"
				title="Customize"
				:icon="Bolt"
				description="Use a customized assistant"
			/>
		</PopoverContent>
	</Popover>
</template>

<script setup lang="ts">
import { api } from "@/client";
import { assistants } from "@/common";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Bolt, List } from "lucide-vue-next";
import { computed, ref } from "vue";
import SelectorAssistantItem from "./SelectorAssistantItem.vue";
import SelectorItem from "./SelectorItem.vue";
import type { AssistantConfig } from "./types";
import { getAssistantIcon } from "./utils";

const isOpen = ref(false);
const selected = defineModel<AssistantConfig>({ required: true });
const emit = defineEmits(["more", "customize"]);

function select(assistant: string) {
	selected.value = { assistant };
	isOpen.value = false;
}

function more() {
	emit("more");
	isOpen.value = false;
}

function customize() {
	emit("customize");
	isOpen.value = false;
}

const preferred_assistants = api.chat.get_preferred_assistants();

const assistants_list = computed(() => {
	const preferred = preferred_assistants.data ?? [];
	if (preferred.includes(selected.value.assistant)) return preferred;

	return [selected.value.assistant, ...preferred];
});

const icon = computed(() => getAssistantIcon(assistants.value[selected.value.assistant]));
// @ts-ignore
const isCustomized = computed(
	() =>
		typeof selected.value.llm !== "undefined" &&
		typeof selected.value.reasoningEffort !== "undefined"
);
</script>
