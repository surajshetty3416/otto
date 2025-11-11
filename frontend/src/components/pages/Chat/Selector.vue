<template>
	<div class="w-full flex gap-2 items-center justify-center">
		<TextLoadingIndicator
			v-if="list_assistants.loading || preferred_assistants.loading"
			text="Loading assistants"
		/>
		<TextLoadingIndicator v-else-if="list_models.loading" text="Loading models" />
		<AssistantSelector
			v-else
			v-model="assistant"
			@more="openConfig = true"
			@customize="openConfig = true"
			@select="select"
		/>
		<AssistantConfigDialog v-model="openConfig" :selected="assistant" @select="select" />
	</div>
</template>

<script setup lang="ts">
import { api, list_assistants, list_models } from "@/client";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import { ref, watch } from "vue";
import AssistantConfigDialog from "./AssistantConfig/AssistantConfigDialog.vue";
import AssistantSelector from "./AssistantSelector.vue";

const openConfig = ref(false);
const preferred_assistants = api.chat.get_preferred_assistants();
const assistant = defineModel<string>({ required: true });

function select(selected: string) {
	assistant.value = selected;
	openConfig.value = false;
}

watch(
	() => preferred_assistants.data,
	(newval) => {
		if (!newval || !newval.length || assistant.value === newval[0]) return;
		assistant.value = newval[0];
	}
);
</script>
