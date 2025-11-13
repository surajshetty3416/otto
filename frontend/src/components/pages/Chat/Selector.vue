<template>
	<div class="flex gap-2 items-center justify-center">
		<TextLoadingIndicator
			v-if="list_assistants.loading || preferred_assistants.loading"
			text="Loading assistants"
		/>
		<TextLoadingIndicator v-else-if="list_models.loading" text="Loading models" />
		<Tooltip v-else>
			<AssistantSelector
				v-model="assistant"
				:disabled="!canChange"
				@more="openConfig"
				@customize="openConfig"
				@select="select"
			/>
			<template #content>
				<div v-if="!canChange" class="p-2">
					<p class="text-sm font-medium mb-1 text-gray-900">{{ details?.title }}</p>
					<p class="flex items-center gap-1 text-xs text-gray-700">
						<Sparkle class="size-3 shrink-0 text-gray-700" stroke-width="1" />
						{{ modelName(details?.llm) }}
						{{ props.settings.llm ? "*" : "" }}
					</p>
					<p
						class="flex items-center gap-1 text-xs text-gray-700 mb-0.5"
						v-if="details?.reasoning_effort !== 'None'"
					>
						<Lightbulb class="size-3 shrink-0 text-gray-700" stroke-width="1" />
						{{ details?.reasoning_effort }}
						{{ props.settings.reasoning_effort ? "*" : "" }}
					</p>
				</div>
				<div v-else>
					<p class="px-2 py-1 text-gray-700 text-sm">Select an assistant to chat with</p>
				</div>
			</template>
		</Tooltip>
		<AssistantConfigDialog v-model="open" :selected="assistant" @select="select" />
	</div>
</template>

<script setup lang="ts">
import { api, list_assistants, list_models } from "@/client";
import { assistants } from "@/common";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import Tooltip from "@/components/ui/tooltip/Tooltip.vue";
import { modelName } from "@/components/utils";
import { Lightbulb, Sparkle } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import AssistantConfigDialog from "./AssistantConfig/AssistantConfigDialog.vue";
import AssistantSelector from "./AssistantSelector.vue";
import type { ChatSettings } from "@/client/generated.types";

const open = ref(false);
const props = defineProps<{ canChange: boolean; settings: ChatSettings }>();
const preferred_assistants = api.chat.get_preferred_assistants();
const assistant = defineModel<string>({ required: true });
const details = computed(() => {
	return assistants.value[assistant.value];
});

function select(selected: string) {
	assistant.value = selected;
	open.value = false;
}

function openConfig() {
	if (!props.canChange) return;
	open.value = true;
}

watch(
	() => preferred_assistants.data,
	(newval) => {
		if (!newval || !newval.length || assistant.value === newval[0]) return;
		assistant.value = newval[0];
	}
);
</script>
