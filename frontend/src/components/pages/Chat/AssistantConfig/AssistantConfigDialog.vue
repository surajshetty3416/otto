<template>
	<Dialog :open="open" @update:open="open = $event">
		<DialogContent no-header class="p-0 max-w-5xl overflow-hidden">
			<DialogTitle class="sr-only">Configure Assistant</DialogTitle>
			<DialogDescription class="sr-only">
				Dialog to select and configure an assistant to use in a new chat
			</DialogDescription>

			<div class="flex h-[600px]" v-if="!list_assistants.loading">
				<!-- Sidebar -->
				<AssistantConfigSidebar v-model="view" :selected="selected" />

				<!-- Main Content -->
				<div v-if="assistant" class="flex-1 flex flex-col">
					<AssistantConfigHeader v-model="open" :assistant="assistant" />
					<AssistantConfigContent :assistant="assistant" />
					<Button
						class="w-fit min-w-18 fixed bottom-4 right-4"
						variant="solid"
						size="md"
						@click="select"
					>
						Use {{ assistant?.title }}
					</Button>
				</div>

				<div v-else class="w-full h-full flex flex-col gap-1 items-center justify-center">
					<h1 class="text-2xl font-semibold">Select an assistant</h1>
					<p class="text-sm text-muted-foreground">
						Select an assistant to view details and configure for your chat
					</p>
				</div>
			</div>
		</DialogContent>
	</Dialog>
</template>

<script setup lang="ts">
import { list_assistants } from "@/client";
import { assistants } from "@/common";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import DialogDescription from "@/components/ui/dialog/DialogDescription.vue";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import { computed, onActivated, onMounted, ref, watch } from "vue";
import type { AssistantConfig } from "../types";
import AssistantConfigContent from "./AssistantConfigContent.vue";
import AssistantConfigHeader from "./AssistantConfigHeader.vue";
import AssistantConfigSidebar from "./AssistantConfigSidebar.vue";
import Button from "@/components/fui/Button/Button.vue";

const props = defineProps<{ selected: AssistantConfig }>();
const emit = defineEmits(["select"]);
const open = defineModel<boolean>({ required: true });
const view = ref<string | null>(null);

function select() {
	if (!view.value) return;
	const config: AssistantConfig = {
		assistant: view.value,
	};
	emit("select", config);
}

function setview() {
	view.value = props.selected.assistant;
}
watch(
	() => props.selected,
	() => setview()
);
onMounted(() => setview());
onActivated(() => setview());
const assistant = computed(() => (view.value ? assistants.value[view.value] : null));
</script>
