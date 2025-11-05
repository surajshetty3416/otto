<template>
	<Menu
		as="div"
		class="relative inline-block text-left w-fit"
		v-slot="{ open }"
		v-if="!isLoading"
	>
		<MenuButton
			v-if="!disabled"
			:title="
				disabled ? 'Start new chat to select a different assistant' : 'Select an assistant'
			"
			:disabled="disabled"
			class="p-2 rounded-md w-fit flex items-center gap-1.5"
			:class="[open ? 'ring-1 ring-gray-200' : '']"
		>
			<Bot class="w-4 h-4 shrink-0 text-gray-700" stroke-width="1" />
			<span class="text-nowrap text-sm text-gray-700">
				{{ assistants[selected.assistant]?.title }}
			</span>
		</MenuButton>
		<button
			v-else
			title="Select an assistant"
			class="p-2 rounded-md w-fit flex items-center gap-1.5"
			@click="showCannotChange"
		>
			<Bot class="w-4 h-4 shrink-0 text-gray-700" stroke-width="1" />
			<span class="text-nowrap text-sm text-gray-700">
				{{ assistants[selected.assistant]?.title }}
			</span>
		</button>

		<transition
			enter-active-class="transition duration-100 ease-out"
			enter-from-class="transform scale-95 opacity-0"
			enter-to-class="transform scale-100 opacity-100"
			leave-active-class="transition duration-75 ease-in"
			leave-from-class="transform scale-100 opacity-100"
			leave-to-class="transform scale-95 opacity-0"
		>
			<MenuItems
				class="absolute right-0 mt-2 origin-top-right divide-y divide-gray-100 rounded-lg bg-white border border-gray-200 shadow-sm w-60 min-w-fit"
			>
				<div class="max-h-60 overflow-y-auto">
					<template
						v-for="assistant in list_assistants.data ?? []"
						:key="assistant.name"
					>
						<MenuItem v-slot="{ active }">
							<button
								@click="select(assistant.name)"
								class="w-full p-1"
								:title="`${assistant.title}\nLLM: ${modelName(
									models[assistant.llm]
								)}\nReasoning Effort: ${assistant.reasoning_effort}`"
							>
								<div
									class="px-1.5 py-1 w-full rounded-md flex items-start"
									:class="[active ? 'bg-gray-100 ' : '']"
								>
									<!-- Icon  -->
									<div
										:title="`Reasoning Effort: ${assistant.reasoning_effort}`"
										class="mt-1 mr-2"
									>
										<Brain
											v-if="assistant.reasoning_effort"
											class="w-4 h-4 shrink-0 text-gray-600"
											stroke-width="1.5"
										/>
										<Zap
											v-else-if="
												['Very Small', 'Small'].includes(
													config(assistant.llm)?.size ?? ''
												)
											"
											class="w-4 h-4 shrink-0 text-gray-600"
											stroke-width="1.5"
										></Zap>
										<Bot
											v-else
											class="w-4 h-4 shrink-0 text-gray-600"
											stroke-width="1.5"
										/>
									</div>

									<!-- Assistant and LLM name -->
									<div class="w-full">
										<p
											class="w-full text-gray-900 font-medium text-base mb-0.5 text-nowrap text-left"
										>
											{{ assistant.title }}
										</p>
										<p class="text-sm text-gray-600 text-left text-nowrap">
											{{ modelName(models[assistant.llm]) }}
										</p>
									</div>

									<!-- Selected -->
									<div
										v-if="selected.assistant === assistant.name"
										class="ml-auto my-auto"
									>
										<Check
											class="w-4 h-4 shrink-0 text-gray-700"
											stroke-width="2"
										/>
									</div>
								</div>
							</button>
						</MenuItem>
					</template>
				</div>

				<MenuItem>
					<button class="w-full p-1" @click="customize">
						<div class="px-1.5 py-1 w-full rounded-md flex items-start">
							<!-- Icon  -->
							<div class="mt-1 mr-2">
								<Bolt class="w-4 h-4 shrink-0 text-gray-600" stroke-width="1.5" />
							</div>

							<!-- Assistant and LLM name -->
							<div class="w-full">
								<p
									class="w-full text-gray-900 font-medium text-base mb-0.5 text-nowrap text-left"
								>
									Customize
								</p>
								<p class="text-sm text-gray-600 text-left text-nowrap">
									Use a customized assistant
								</p>
							</div>
						</div>
					</button>
				</MenuItem>
			</MenuItems>
		</transition>
	</Menu>
</template>

<script setup lang="ts">
import { list_assistants, list_models } from "@/client";
import type { ModelDetails } from "@/client/generated.types";
import { assistants, models } from "@/common";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/vue";
import { Bolt, Bot, Brain, Check, Zap } from "lucide-vue-next";
import { computed } from "vue";
import { toast } from "vue-sonner";
import type { AssistantConfig } from "./types";
import { modelName } from "@/components/utils";

defineProps({
	disabled: {
		type: Boolean,
		default: false,
	},
});

const selected = defineModel<AssistantConfig>({ required: true });

function select(assistant: string) {
	selected.value = { assistant };
}

function config(llm: string): ModelDetails | undefined {
	return models.value[llm];
}

function customize() {
	toast.info("Implement this!");
	console.log("customize");
}

const isLoading = computed(() => {
	return list_assistants.loading || list_models.loading;
});

// @ts-ignore
const isCustomized = computed(
	() =>
		typeof selected.value.llm !== "undefined" &&
		typeof selected.value.reasoningEffort !== "undefined"
);

function showCannotChange() {
	toast.warning("Cannot change assistant", {
		description: "Start a new chat to change the assistant",
	});
}
</script>
<style scoped></style>
