t
<template>
	<Dialog :open="open" @update:open="open = $event">
		<DialogContent class="h-[38vh]">
			<!-- Dialog Header -->
			<template #header>
				<DialogTitle class="flex w-full items-center gap-2">
					<Settings class="h-4 w-4 text-gray-900" stroke-width="1.75" />
					Chat Settings
					<TextLoadingIndicator
						v-if="save_settings.loading"
						class="ml-auto mr-4"
						text="Saving"
					/>
				</DialogTitle>
			</template>

			<!-- Dialog Body -->
			<DialogDescription class="mb-6">
				Configure settings for this chat to override the defaults set for
				<TextTooltip
					v-if="assistant.title"
					:content="`${assistant.title} is the selected assistant`"
				>
					<span v-if="assistant.title" class="font-medium">
						{{ assistant?.title }}
					</span>
				</TextTooltip>
				<span v-else> this assistant </span>.
			</DialogDescription>

			<div v-if="pane === 'config'" class="flex flex-col gap-6">
				<SettingsItem :icon="Sparkle" label="Model" :description="modelDescription">
					<LlmSelect v-model="settings.llm" />
				</SettingsItem>

				<hr class="border-gray-200" />
				<SettingsItem
					:icon="Wrench"
					label="Tool Permissions"
					:description="toolPermissionsDescription"
				>
					<ToolPermissionsSelect v-model="settings.tool_permissions" />
				</SettingsItem>

				<SettingsItem
					:icon="Lightbulb"
					label="Reasoning Effort"
					:description="reasoningEffortDescription"
				>
					<ReasoningEffortSelect
						v-model="settings.reasoning_effort"
						:disabled="!canReason"
					/>
				</SettingsItem>

				<SettingsItem :icon="Smile" label="YOLO Mode">
					<Switch :modelValue="yoloMode" @change="toggleYoloMode" />
				</SettingsItem>
			</div>

			<div v-else-if="pane === 'prompt'" class="flex flex-col gap-6">
				<div>
					<Textarea
						placeholder="Enter custom instructions for this assistant"
						class="resize-none"
						v-model="settings.user_directives"
						:disabled="!assistant?.supports_user_directives"
						:rows="8"
					/>

					<div class="mt-1 flex items-center gap-1">
						<template v-for="tip in Object.keys(customInstructionTips)" :key="tip">
							<button
								class="rounded-full border border-gray-200 px-1.5 py-0.5 text-sm hover:bg-gray-100"
								:class="tipClass(tip)"
								@click="toggleTip(tip)"
							>
								{{ tip }}
							</button>
						</template>
					</div>
				</div>
				<p
					v-if="!assistant?.supports_user_directives"
					class="flex items-center gap-2 text-sm text-gray-500"
				>
					<span>
						<AlertTriangle class="size-3.5 text-yellow-500" />
					</span>
					{{ assistant?.title || "This assistant" }} does not support custom
					instructions.
				</p>
			</div>

			<!-- Dialog Footer -->
			<template #buttons>
				<button
					class="mr-auto p-0 text-sm text-gray-800 hover:text-gray-900"
					@click="pane = pane === 'config' ? 'prompt' : 'config'"
				>
					{{ pane == "config" ? "Customize Prompt" : "Customize Config" }}
				</button>
				<Button variant="outline" size="md" @click="reset">Reset</Button>
			</template>
		</DialogContent>
	</Dialog>
</template>

<script setup lang="ts">
import type { ChatSettings } from "@/client/generated.types";
import { assistants, models } from "@/common";
import Button from "@/components/fui/Button/Button.vue";
import { Switch } from "@/components/fui/Switch";
import Textarea from "@/components/fui/Textarea/Textarea.vue";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import DialogDescription from "@/components/ui/dialog/DialogDescription.vue";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import TextTooltip from "@/components/ui/tooltip/TextTooltip.vue";
import { modelName } from "@/components/utils";
import { AlertTriangle, Lightbulb, Settings, Smile, Sparkle, Wrench } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import { toast } from "vue-sonner";
import { save_settings } from "../utils";
import LlmSelect from "./LlmSelect.vue";
import ReasoningEffortSelect from "./ReasoningEffortSelect.vue";
import SettingsItem from "./SettingsItem.vue";
import ToolPermissionsSelect from "./ToolPermissionsSelect.vue";

const customInstructionTips: Record<string, string> = {
	Direct: "Be specific and to the point.",
	Concise: "Keep your responses short.",
	Friendly: "Be friendly and engaging.",
	Unhinged: "Be completely insane and unpredictable.",
};

const pane = ref<"config" | "prompt">("config");
const open = defineModel<boolean>({ required: true });
const props = defineProps<{ assistant: string }>();
const settings = defineModel<ChatSettings>("settings", { required: true });

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

	settings.value.tool_permissions = "Default";
	settings.value.reasoning_effort = null;
	settings.value.llm = null;
	settings.value.user_directives = "";
}

const isDefault = computed(() => {
	return (
		(settings.value.tool_permissions === null ||
			settings.value.tool_permissions === "Default") &&
		(settings.value.user_directives === null || settings.value.user_directives === "") &&
		settings.value.reasoning_effort === null &&
		settings.value.llm === null
	);
});

const toolPermissionsDescription = computed(() => {
	switch (settings.value.tool_permissions) {
		case "Allow All":
			return "All tools will run without user permission";
		case "Allow Readonly":
			return "Read only tools will run without user permission";
		case "Ask For All":
			return "All tools will require user permission";
		case "Ask For Non Readonly":
			return "Non readonly tools will require user permission";
		case "Default":
		default:
			return "Tools requiring user permission will raise requests";
	}
});

const reasoningEffortDescription = computed(() => {
	if (!canReason.value) {
		return "Selected model does not support reasoning";
	}

	switch (settings.value.reasoning_effort) {
		case "Low":
		case "Medium":
		case "High":
			return `Assistant will use ${settings.value.reasoning_effort} reasoning effort`;
		case "None":
			return "Assistant will not use reasoning";
		default:
			return `Assistant will use the default reasoning effort (${
				defaults.value.reasoning_effort ?? "Medium"
			})`;
	}
});

const modelDescription = computed(() => {
	if (!settings.value.llm && !defaults.value.llm) return "Assistant will use the default model";
	if (!settings.value.llm && defaults.value.llm)
		return `Assistant will use the default model (${modelName(defaults.value.llm)})`;
	return `Assistant will use ${modelName(settings.value.llm!)}`;
});

const assistant = computed(() => {
	return assistants.value[props.assistant];
});

const canReason = computed(() => {
	return models.value[settings.value.llm ?? defaults.value.llm ?? ""]?.is_reasoning ?? true;
});

const yoloMode = computed(() => {
	return (
		settings.value.tool_permissions === "Allow All" &&
		settings.value.reasoning_effort === "High"
	);
});

watch(open, (newval, oldval) => {
	// Reset values when dialog is closed
	if (newval === true && oldval === false) return;
	setTimeout(() => {
		pane.value = "config";
	}, 100);
});

function isTipSet(tip: string) {
	return settings.value.user_directives?.includes(customInstructionTips[tip]);
}

function toggleYoloMode(checked: boolean) {
	settings.value.tool_permissions = checked ? "Allow All" : "Default";
	if (canReason.value) {
		settings.value.reasoning_effort = checked ? "High" : null;
	}
}

function tipClass(tip: string) {
	const isSet = isTipSet(tip);
	return [
		isSet ? "text-gray-800" : "text-gray-700",
		isSet ? "border-gray-300" : "border-gray-200",
		isSet ? "bg-gray-200" : "bg-gray-50",
	];
}

function toggleTip(tip: string) {
	if (!assistant?.value?.supports_user_directives) return;

	if (isTipSet(tip)) {
		settings.value.user_directives =
			settings.value.user_directives?.replace(customInstructionTips[tip], "").trim() ?? null;
	} else {
		settings.value.user_directives = [
			settings.value.user_directives,
			customInstructionTips[tip],
		]
			.join(" ")
			.trim();
	}
}
</script>
