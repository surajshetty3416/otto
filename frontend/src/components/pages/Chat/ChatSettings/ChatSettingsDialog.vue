<template>
	<Dialog :open="open" @update:open="open = $event">
		<DialogContent>
			<template #header>
				<DialogTitle class="flex items-center gap-2">
					<Settings class="w-4 h-4 text-gray-900" stroke-width="1.75" />
					Chat Settings</DialogTitle
				>
			</template>

			<p class="text-base text-gray-900">Edit chat settings here.</p>

			<template #buttons>
				<Button variant="solid" size="md" @click="reset" autofocus>Reset</Button>
			</template>
		</DialogContent>
	</Dialog>
</template>

<script setup lang="ts">
import type { ChatSettings } from "@/client/generated.types";
import { assistants } from "@/common";
import Button from "@/components/fui/Button/Button.vue";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import { Settings } from "lucide-vue-next";
import { computed } from "vue";

const open = defineModel<boolean>({ required: true });
const props = defineProps<{
	chatId?: string;
	assistant: string;
	isNew: boolean;
	settings: ChatSettings | undefined;
}>();

const emit = defineEmits<{ (e: "save", settings: ChatSettings): void }>();
const defaults = computed(() => {
	const ast = assistants.value[props.assistant];

	return {
		llm: ast?.llm || null,
		reasoning_effort: ast?.reasoning_effort || null,
		tool_permissions: "Default",
		user_directives: null,
	} as ChatSettings;
});

function reset() {}
</script>
