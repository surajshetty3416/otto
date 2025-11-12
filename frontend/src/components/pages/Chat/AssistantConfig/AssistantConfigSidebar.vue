<template>
	<div class="w-56 border-r border-gray-200 flex flex-col bg-gray-25">
		<!-- Sidebar Header -->
		<div class="p-4 mb-4">
			<h2 class="text-lg font-semibold py-1">Select Assistant</h2>
		</div>

		<!-- Assistant List -->
		<div class="flex-1 overflow-y-auto flex flex-col gap-2 w-full">
			<button
				v-for="assistant in list_assistants.data ?? []"
				:key="assistant.name"
				@click="view = assistant.name"
				class="flex mx-2 p-2 gap-2 rounded-lg hover:bg-gray-50 outline-none"
				:class="{
					'bg-gray-100': view === assistant.name,
				}"
			>
				<component
					:is="getAssistantIcon(assistant)"
					class="w-3.5 h-3.5 shrink-0 text-gray-700"
					stroke-width="1.5"
				/>
				<div class="flex flex-col items-start justify-center">
					<div class="font-medium text-sm">{{ assistant.title }}</div>
					<div class="text-xs text-muted-foreground mt-1">
						{{ modelName(assistant.llm) }}
					</div>
				</div>
				<Check
					v-if="selected === assistant.name"
					class="w-3.5 h-3.5 shrink-0 text-gray-700 ml-auto my-auto"
					stroke-width="1.5"
				/>
			</button>
		</div>
	</div>
</template>
<script lang="ts" setup>
import { list_assistants } from "@/client";
import { modelName } from "@/components/utils";
import { Check } from "lucide-vue-next";
import { getAssistantIcon } from "../utils";

const view = defineModel<string | null>({ required: true });
defineProps<{ selected: string }>();
</script>
