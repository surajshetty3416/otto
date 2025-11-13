<template>
	<Link
		doctype="Otto Chat"
		fieldname="llm"
		:fields="['provider', 'size', 'is_reasoning']"
		:search-fields="['provider', 'size', 'reasoning']"
		size="sm"
		v-model="modelValue"
		variant="ghost"
		:transform="llmOptionsTransform"
		placeholder="Select model"
	>
		<template #trigger>
			<slot name="trigger"></slot>
		</template>
		<template v-slot="{ options, select, cursor }">
			<div class="flex max-h-56 min-w-32 flex-col overflow-y-auto p-1">
				<template v-for="(option, index) in options" :key="option.value">
					<div
						:data-index="index"
						@click="select(option)"
						class="flex cursor-pointer items-center justify-between rounded-md px-2 py-1.5 text-base text-gray-800 hover:bg-gray-100"
						:class="[{ 'bg-gray-100': cursor === index }]"
					>
						<div class="flex flex-col">
							<p class="font-medium mb-1">
								{{ option.label }}
							</p>

							<p
								class="flex items-center gap-2 text-xs text-gray-700 font-normal mb-0.5"
							>
								<span>{{ option.item?.provider }}</span>
								<span>{{ option.item?.size }}</span>
								<span>{{ option.item?.reasoning }}</span>
							</p>
							<p class="text-xs text-ink-gray-3">
								{{ option.value }}
							</p>
						</div>
						<Check
							v-if="option.value === modelValue"
							class="size-3.5 shrink-0 p-0 text-gray-700"
						/>
					</div>
				</template>
			</div>
		</template>
	</Link>
</template>

<script setup lang="ts">
import Link from "@/components/ui/Link/Link.vue";
import type { ComboboxOption } from "@/components/ui/combobox/types";
import { modelName } from "@/components/utils";
import { Check } from "lucide-vue-next";

const modelValue = defineModel<string | null>({ required: true });

function llmOptionsTransform(option: ComboboxOption) {
	const item = { ...option.item };
	item.reasoning = option.item?.is_reasoning ? "Reasoning" : "";
	return {
		label: modelName(option.value),
		value: option.value,
		item,
	};
}
</script>
