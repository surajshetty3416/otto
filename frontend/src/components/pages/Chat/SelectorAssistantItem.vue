<template>
	<SelectorItem
		:title="assistant_.title"
		:icon="icon"
		:description="modelName(model)"
		:selected="selected === assistant"
		:active="active"
	/>
</template>
<script setup lang="ts">
import { assistants, models } from "@/common";
import { modelName } from "@/components/utils";
import { computed } from "vue";
import SelectorItem from "./SelectorItem.vue";
import { getAssistantIcon } from "./utils";

const props = defineProps<{
	active: boolean;
	assistant: string;
	selected: string;
}>();

const assistant_ = computed(() => assistants.value[props.assistant]);
const model = computed(() => models.value[assistant_.value?.llm]);
const icon = computed(() => getAssistantIcon(assistant_.value));
</script>
