<template>
	<Dialog :open="open" @update:open="open = $event">
		<DialogContent>
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
			<div class="flex flex-col gap-4">
				<SettingsItem
					:icon="Wrench"
					label="Tool Permissions"
					:description="toolPermissionsDescription"
				>
					<Select
						class="w-44"
						name="tool_permissions"
						doctype="Otto Chat"
						fieldname="tool_permissions"
						placeholder="Select option"
						v-model="delta.tool_permissions"
						size="xs"
						variant="outline"
					>
					</Select>
				</SettingsItem>

				<SettingsItem
					:icon="Brain"
					label="Reasoning Effort"
					:description="reasoningEffortDescription"
				>
					<Select
						class="w-44"
						doctype="Otto Chat"
						fieldname="reasoning_effort"
						placeholder="Select option"
						v-model="delta.reasoning_effort"
						size="xs"
						variant="outline"
						:disabled="!canReason"
					>
					</Select>
				</SettingsItem>

				<SettingsItem :icon="Smile" label="YOLO Mode">
					<Switch v-model="yoloMode" />
				</SettingsItem>

				<hr class="border-gray-200" />
				<SettingsItem
					:icon="Sparkle"
					label="Model"
					description="Select the model to use for this chat"
				>
					<Select
						doctype="Otto Chat"
						fieldname="reasoning_effort"
						placeholder="Select option"
						v-model="delta.reasoning_effort"
						variant="outline"
					>
					</Select>
				</SettingsItem>
			</div>

			<!-- 

			TODO:
			tomorrow:
			- follow similar design as macos system settings
			- add settings for custom llm (needs component)
			- add checkbox for yolo mode (needs, component, reasoning high, tool permissions allow all)
			- add settings for custom user directives (needs component)
			- add settings for tool selection (different pane/tab)
			- show custom settings (directives, reasoning, perms) below chat input (allow shortcut toggling)
			- show selected assistant and llm in the header or somewhere
			- move info, archive, and delete to a 3 dot menu
			- add info (thumbs up and down) button under a chat turn
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
import { assistants, models } from "@/common";
import Button from "@/components/fui/Button/Button.vue";
import Select from "@/components/fui/Select/Select.vue";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import DialogDescription from "@/components/ui/dialog/DialogDescription.vue";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import { Brain, Settings, Smile, Sparkle, Wrench } from "lucide-vue-next";
import { computed, reactive, ref, watch } from "vue";
import { toast } from "vue-sonner";
import { save_settings } from "../utils";
import SettingsItem from "./SettingsItem.vue";
import { Switch } from "@/components/fui/Switch";

const yoloMode = ref(false);
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
	if (isDefault.value || !isDirty.value) {
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
	if (!canReason.value) {
		return "Selected model does not support reasoning";
	}

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

const canReason = computed(() => {
	return models.value[delta.llm ?? defaults.value.llm ?? ""]?.is_reasoning ?? true;
});

watch(yoloMode, (newVal) => {
	delta.tool_permissions = newVal ? "Allow All" : null;
	if (canReason.value) {
		delta.reasoning_effort = newVal ? "High" : null;
	}
});

watch(
	() => [delta.tool_permissions, delta.reasoning_effort],
	([toolPermissions, reasoningEffort]) => {
		if (canReason.value && toolPermissions === "Allow All" && reasoningEffort === "High") {
			yoloMode.value = true;
		} else if (!canReason.value && toolPermissions === "Allow All") {
			yoloMode.value = true;
		} else {
			yoloMode.value = false;
		}
	}
);
</script>
