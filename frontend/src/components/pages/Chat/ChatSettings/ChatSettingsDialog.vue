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

					<p v-else-if="isDirty" class="ml-auto mr-4 text-xs text-gray-500">
						Unsaved Changes
					</p>
				</DialogTitle>
			</template>

			<!-- Dialog Body -->
			<DialogDescription class="mb-6">
				Configure chat settings to override defaults set for
				<span class="font-medium"> {{ assistant?.title ?? "Assistant" }} </span>.
			</DialogDescription>

			<div v-if="pane === 'config'" class="flex flex-col gap-6">
				<SettingsItem :icon="Sparkle" label="Model" :description="modelDescription">
					<Link
						doctype="Otto Chat"
						fieldname="llm"
						:fields="['provider', 'size', 'is_reasoning']"
						size="sm"
						v-model="delta.llm"
						variant="ghost"
						:transform="llmOptionsTransform"
						placeholder="Select model"
					>
						<template v-slot="{ options, select, cursor }">
							<div class="flex max-h-56 min-w-32 flex-col gap-2 overflow-y-auto p-1">
								<template v-for="(option, index) in options" :key="option.value">
									<div
										:data-index="index"
										@click="select(option)"
										class="flex cursor-pointer items-center justify-between rounded-md px-2 py-1.5 text-base text-gray-800 hover:bg-gray-100"
										:class="[{ 'bg-gray-100': cursor === index }]"
									>
										<div class="flex flex-col gap-1.5">
											<p class="font-medium">
												{{ option.label }}
											</p>

											<p
												class="flex items-center gap-1 text-xs text-gray-700"
											>
												<span class="">{{ option.item?.provider }}</span>
												<span class="">{{ option.item?.size }}</span>
												<span class="" v-if="option.item?.reasoning">{{
													option.item?.reasoning
												}}</span>
											</p>
											<p class="text-sm text-ink-gray-5">
												{{ option.value }}
											</p>
										</div>
										<Check
											v-if="option.value === delta.llm"
											class="size-3.5 shrink-0 p-0 text-gray-700"
										/>
									</div>
								</template>
							</div>
						</template>
					</Link>
				</SettingsItem>

				<hr class="border-gray-200" />
				<SettingsItem
					:icon="Wrench"
					label="Tool Permissions"
					:description="toolPermissionsDescription"
				>
					<Select
						doctype="Otto Chat"
						fieldname="tool_permissions"
						placeholder="Select option"
						v-model="delta.tool_permissions"
						size="xs"
						variant="ghost"
					>
					</Select>
				</SettingsItem>

				<SettingsItem
					:icon="Lightbulb"
					label="Reasoning Effort"
					:description="reasoningEffortDescription"
				>
					<Select
						doctype="Otto Chat"
						fieldname="reasoning_effort"
						placeholder="Select effort"
						v-model="delta.reasoning_effort"
						size="xs"
						variant="ghost"
						:disabled="!canReason"
					>
					</Select>
				</SettingsItem>

				<SettingsItem :icon="Smile" label="YOLO Mode">
					<Switch v-model="yoloMode" />
				</SettingsItem>
			</div>

			<div v-else-if="pane === 'prompt'" class="flex flex-col gap-6">
				<div>
					<Textarea
						placeholder="Enter custom instructions for this assistant"
						class="resize-none"
						v-model="delta.user_directives"
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
import { Switch } from "@/components/fui/Switch";
import Textarea from "@/components/fui/Textarea/Textarea.vue";
import type { ComboboxOption } from "@/components/ui/combobox/types";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import DialogDescription from "@/components/ui/dialog/DialogDescription.vue";
import DialogTitle from "@/components/ui/dialog/DialogTitle.vue";
import Link from "@/components/ui/Link/Link.vue";
import Select from "@/components/ui/Select/Select.vue";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import { modelName } from "@/components/utils";
import {
	AlertTriangle,
	Check,
	Lightbulb,
	Settings,
	Smile,
	Sparkle,
	Wrench,
} from "lucide-vue-next";
import { computed, reactive, ref, watch, watchEffect } from "vue";
import { toast } from "vue-sonner";
import { save_settings } from "../utils";
import SettingsItem from "./SettingsItem.vue";

const customInstructionTips: Record<string, string> = {
	Direct: "Be specific and to the point.",
	Concise: "Keep your responses short.",
	Friendly: "Be friendly and engaging.",
	Unhinged: "Be completely insane and unpredictable.",
};

const pane = ref<"config" | "prompt">("config");
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
	if (isDefault.value && !isDirty.value) {
		toast.info("Settings already at default");
		return;
	}

	delta.tool_permissions = "Default";
	delta.reasoning_effort = null;
	delta.llm = null;
	delta.user_directives = "";
	emit("save", delta);
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
		delta.tool_permissions === null ||
		(delta.tool_permissions === "Default" &&
			delta.reasoning_effort === null &&
			delta.llm === null &&
			delta.user_directives === null) ||
		delta.user_directives === ""
	);
});

const isDirty = computed(() => {
	return (
		(delta.tool_permissions ?? "Default") !==
			(props.settings?.tool_permissions ?? "Default") ||
		delta.reasoning_effort !== props.settings?.reasoning_effort ||
		delta.llm !== props.settings?.llm ||
		(delta.user_directives ?? "") !== (props.settings?.user_directives ?? "")
	);
});

const toolPermissionsDescription = computed(() => {
	switch (delta.tool_permissions) {
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

	switch (delta.reasoning_effort) {
		case "Low":
		case "Medium":
		case "High":
			return `Assistant will use ${delta.reasoning_effort} reasoning effort`;
		case "None":
			return "Assistant will not use reasoning";
		default:
			return `Assistant will use the default reasoning effort (${
				defaults.value.reasoning_effort ?? "Medium"
			})`;
	}
});

const modelDescription = computed(() => {
	if (!delta.llm && !defaults.value.llm) return "Assistant will use the default model";
	if (!delta.llm && defaults.value.llm)
		return `Assistant will use the default model (${modelName(defaults.value.llm)})`;
	return `Assistant will use ${modelName(delta.llm!)}`;
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

watchEffect(() => {
	delta.tool_permissions = props.settings?.tool_permissions ?? "Default";
	delta.reasoning_effort = props.settings?.reasoning_effort ?? null;
	delta.llm = props.settings?.llm ?? null;
	delta.user_directives = props.settings?.user_directives ?? "";
});

watch(open, (newval, oldval) => {
	// Reset values when dialog is closed
	if (newval === true && oldval === false) return;
	setTimeout(() => {
		pane.value = "config";
		delta.tool_permissions = props.settings?.tool_permissions ?? "Default";
		delta.reasoning_effort = props.settings?.reasoning_effort ?? null;
		delta.llm = props.settings?.llm ?? null;
		delta.user_directives = props.settings?.user_directives ?? null;
	}, 100);
});

function llmOptionsTransform(option: ComboboxOption) {
	const item = { ...option.item };
	item.reasoning = option.item?.is_reasoning ? "Reasoning" : "";
	return {
		label: modelName(option.value),
		value: option.value,
		item,
	};
}

function isTipSet(tip: string) {
	return delta.user_directives?.includes(customInstructionTips[tip]);
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
		delta.user_directives =
			delta.user_directives?.replace(customInstructionTips[tip], "").trim() ?? null;
	} else {
		delta.user_directives = [delta.user_directives, customInstructionTips[tip]]
			.join(" ")
			.trim();
	}
}
</script>
