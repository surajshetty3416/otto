<template>
	<div v-if="anyCustom" class="text-gray-400 font-bold">·</div>

	<TextTooltip
		v-if="customModel"
		:content="`Custom model: ${modelName(settings.llm!)}`"
		:delay="500"
	>
		<LlmSelect v-model="settings.llm">
			<template #trigger>
				<button class="indicator-button">
					<Sparkle stroke-width="1" />
					{{ modelName(settings.llm!) }}
				</button>
			</template>
		</LlmSelect>
	</TextTooltip>

	<TextTooltip
		v-if="customReasoningEffort"
		:content="`Custom reasoning effort: ${settings.reasoning_effort}`"
		:keybinds="keybinds['cycle-reasoning-effort']"
		:delay="500"
	>
		<ReasoningEffortSelect v-model="settings.reasoning_effort">
			<template #trigger>
				<button class="indicator-button">
					<Lightbulb stroke-width="1" />
					Reasoning {{ settings.reasoning_effort }}
				</button>
			</template>
		</ReasoningEffortSelect>
	</TextTooltip>

	<TextTooltip
		v-if="customToolPermissions"
		:content="`Custom tool permissions: ${settings.tool_permissions}`"
		:keybinds="keybinds['cycle-tool-permissions']"
		:delay="500"
	>
		<ToolPermissionsSelect v-model="settings.tool_permissions">
			<template #trigger>
				<button class="indicator-button">
					<Wrench stroke-width="1" />
					{{ settings.tool_permissions }}
				</button>
			</template>
		</ToolPermissionsSelect>
	</TextTooltip>

	<TextTooltip
		v-if="customUserDirectives"
		content="Custom instructions are set for this chat"
		:delay="500"
	>
		<button class="indicator-button">
			<Pencil stroke-width="1" />
			Custom Instruction
		</button>
	</TextTooltip>
</template>
<script setup lang="ts">
import type { ChatSettings } from "@/client/generated.types";
import { assistants } from "@/common";
import TextTooltip from "@/components/ui/tooltip/TextTooltip.vue";
import { modelName } from "@/components/utils";
import { keybinds } from "@/shortcuts";
import { Lightbulb, Pencil, Sparkle, Wrench } from "lucide-vue-next";
import { computed } from "vue";
import LlmSelect from "./ChatSettings/LlmSelect.vue";
import ReasoningEffortSelect from "./ChatSettings/ReasoningEffortSelect.vue";
import ToolPermissionsSelect from "./ChatSettings/ToolPermissionsSelect.vue";

const props = defineProps<{ assistant: string }>();
const settings = defineModel<ChatSettings>({ required: true });
const details = computed(() => assistants.value[props.assistant]);

const customModel = computed(() => {
	if (!settings.value.llm) return false;
	return settings.value.llm !== details.value?.llm;
});

const customReasoningEffort = computed(() => {
	if (!settings.value.reasoning_effort) return false;
	return settings.value.reasoning_effort !== details.value?.reasoning_effort;
});

const customUserDirectives = computed(() => {
	return !!settings.value.user_directives;
});

const customToolPermissions = computed(() => {
	return !(settings.value.tool_permissions === "Default" || !settings.value.tool_permissions);
});

const anyCustom = computed(() => {
	return (
		customModel.value ||
		customReasoningEffort.value ||
		customUserDirectives.value ||
		customToolPermissions.value
	);
});
</script>
<style scoped></style>
