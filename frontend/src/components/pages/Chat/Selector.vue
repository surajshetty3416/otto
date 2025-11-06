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
		<AssistantConfigDialog v-model="openConfig" :selected="assistant" />
	</div>
</template>

<script setup lang="ts">
import { api, list_assistants, list_models } from "@/client";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import AssistantSelector from "./AssistantSelector.vue";
import type { AssistantConfig } from "./types";
import AssistantConfigDialog from "./AssistantConfig/AssistantConfigDialog.vue";
import { ref } from "vue";

const openConfig = ref(true);
const preferred_assistants = api.chat.get_preferred_assistants();
const assistant = defineModel<AssistantConfig>({ required: true });

function select(selected: AssistantConfig) {
	assistant.value = selected;
	openConfig.value = false;
}

/**
 * fetch user preferred assistant (select this)
 * show more if there are more assistants to be shown
 * clicking on customize will open the customize modal
 *
 * show assistant details in the more section
 *
 * show selected assistant in the header once chat starts (don't show it in the input)
 *
 * after chat starts header should have a gear icon to config mid chat configurable options
 *
 * input bar should only have input related things, add a + button for images, files, etc
 */
</script>
