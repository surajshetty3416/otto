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
import Button from "@/components/fui/Button/Button.vue";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import { Settings } from "lucide-vue-next";

const open = defineModel<boolean>({ required: true });
const props = defineProps<{
	chatId?: string;
	isNew: boolean;
}>();

function reset() {}
</script>
