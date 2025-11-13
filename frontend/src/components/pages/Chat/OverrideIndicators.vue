<template>
	<div v-if="anyCustom" class="text-gray-400 font-bold">·</div>
	<div v-if="customLLM" class="indicator">
		<Sparkle class="indicator-icon" stroke-width="1" />
		{{ modelName(details?.llm) }}
	</div>
	<div v-if="customReasoningEffort" class="indicator">
		<Lightbulb class="indicator-icon" stroke-width="1" />
		Reasoning {{ details?.reasoning_effort }}
	</div>
	<div v-if="customToolPermissions" class="indicator">
		<Wrench class="indicator-icon" stroke-width="1" />
		{{ props.settings.tool_permissions }}
	</div>
	<div v-if="customUserDirectives" class="indicator">
		<Pencil class="indicator-icon" stroke-width="1" />
		Custom Instruction
	</div>
</template>
<script setup lang="ts">
import type { ChatSettings } from "@/client/generated.types";
import { assistants } from "@/common";
import { modelName } from "@/components/utils";
import { Lightbulb, Pencil, Sparkle, Wrench } from "lucide-vue-next";
import { computed } from "vue";

const props = defineProps<{ settings: ChatSettings; assistant: string }>();
const details = computed(() => assistants.value[props.assistant]);

const customLLM = computed(() => {
	if (!props.settings.llm) return false;
	return props.settings.llm !== details.value?.llm;
});

const customReasoningEffort = computed(() => {
	if (!props.settings.reasoning_effort) return false;
	return props.settings.reasoning_effort !== details.value?.reasoning_effort;
});

const customUserDirectives = computed(() => {
	return !!props.settings.user_directives;
});

const customToolPermissions = computed(() => {
	return !(props.settings.tool_permissions === "Default" || !props.settings.tool_permissions);
});

const anyCustom = computed(() => {
	return (
		customLLM.value ||
		customReasoningEffort.value ||
		customUserDirectives.value ||
		customToolPermissions.value
	);
});
</script>
<style scoped>
.indicator {
	@apply text-sm border px-1.5 py-1 rounded flex items-center gap-1 bg-white/85 backdrop-blur-lg shrink-0;
}

.indicator-icon {
	@apply size-3 shrink-0 text-gray-700 -ml-0.5;
}
</style>
