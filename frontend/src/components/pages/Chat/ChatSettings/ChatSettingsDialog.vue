<template>
	<Dialog :open="open" @update:open="open = $event">
		<DialogContent class="max-w-3xl">
			<template #header>
				<DialogTitle class="flex items-center gap-2 w-full">
					<Settings class="w-4 h-4 text-gray-900" stroke-width="1.75" />
					Chat Settings
					<TextLoadingIndicator
						v-if="save_settings.loading"
						class="ml-auto mr-4"
						text="Saving"
					/>
					<p v-else-if="isDirty" class="text-xs text-gray-500 ml-auto mr-4">
						Unsaved Changes
					</p>
				</DialogTitle>
			</template>

			<DialogDescription>
				Configure chat settings to override defaults set for
				<span class="font-medium">{{ assistant?.title ?? "ssistant" }}</span
				>.
			</DialogDescription>

			<div class="grid grid-cols-2 gap-4">
				<Select
					:show-label="true"
					doctype="Otto Chat"
					fieldname="tool_permissions"
					placeholder="Select an option to override default"
					v-model="delta.tool_permissions"
					:description="toolPermissionsDescription"
				>
					<template #prefix>
						<Wrench class="w-4 h-4 text-gray-500" stroke-width="1.5" />
					</template>
				</Select>

				<Select
					:show-label="true"
					doctype="Otto Chat"
					fieldname="reasoning_effort"
					:placeholder="`Select an option to override default`"
					v-model="delta.reasoning_effort"
					:description="reasoningEffortDescription"
				>
					<template #prefix>
						<Brain class="w-4 h-4 text-gray-500" stroke-width="1.5" />
					</template>
				</Select>
			</div>

			<!-- 

			TODO:
			- add settings for custom user directives (needs component)
			- add settings for custom llm (needs component)
			- add checkbox for yolo mode (reasoning high, tool permissions allow all)
			- add settings for tool selection
			- show custom settings below chat input (allow shortcut toggling)
			-->

			<template #buttons>
				<Button variant="outline" size="md" @click="reset" autofocus>Reset</Button>
				<Button variant="solid" size="md" @click="save" autofocus>Save</Button>
			</template>
		</DialogContent>
	</Dialog>
</template>

<script setup lang="ts">
import type { ChatSettings } from "@/client/generated.types";
import { assistants } from "@/common";
import Button from "@/components/fui/Button/Button.vue";
import Select from "@/components/fui/Select/Select.vue";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import DialogDescription from "@/components/ui/dialog/DialogDescription.vue";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import { Brain, Settings, Wrench } from "lucide-vue-next";
import { computed, reactive } from "vue";
import { toast } from "vue-sonner";
import { save_settings } from "../utils";

const open = defineModel<boolean>({ required: true });
const props = defineProps<{
	chatId?: string;
	assistant: string;
	isNew: boolean;
	settings: ChatSettings | undefined;
}>();

const delta = reactive<ChatSettings>({
	tool_permissions: null,
	user_directives: null,
	reasoning_effort: null,
	llm: null,
});

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

function reset() {
	if (isDefault.value) {
		toast.info("Settings already at default");
		return;
	}

	delta.tool_permissions = null;
	delta.reasoning_effort = null;
	delta.llm = null;
	delta.user_directives = null;
}

function save() {
	if (!isDirty.value) {
		toast.info("No changes to save");
		return;
	}

	emit("save", delta);
	open.value = false;
}

const isDefault = computed(() => {
	return (
		(delta.tool_permissions === null || delta.tool_permissions === "Default") &&
		delta.reasoning_effort === null &&
		delta.llm === null &&
		delta.user_directives === null
	);
});

const isDirty = computed(() => {
	return (
		delta.tool_permissions !== props.settings?.tool_permissions ||
		delta.reasoning_effort !== props.settings?.reasoning_effort ||
		delta.llm !== props.settings?.llm ||
		delta.user_directives !== props.settings?.user_directives
	);
});

const toolPermissionsDescription = computed(() => {
	switch (delta.tool_permissions) {
		case "Allow All":
			return "All tools will run without user permission";
		case "Allow Readonly":
			return "Read only tools will run without user permission";
		case "Ask For All":
			return "All tool uses will require user permission";
		case "Ask For Non Readonly":
			return "Non readonly tool uses will require user permission";
		case "Default":
		default:
			return "Tools requiring user permission will raise requests";
	}
});

const reasoningEffortDescription = computed(() => {
	switch (delta.reasoning_effort) {
		case "Low":
		case "Medium":
		case "High":
			return `Model will use ${delta.reasoning_effort} reasoning effort`;
		case "None":
			return "Model will not use reasoning";
		default:
			return `Model will use default reasoning effort (${
				defaults.value.reasoning_effort ?? "Medium"
			})`;
	}
});

const assistant = computed(() => {
	return assistants.value[props.assistant];
});
</script>
