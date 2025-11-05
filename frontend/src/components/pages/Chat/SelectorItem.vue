<template>
	<button class="w-full p-1">
		<div
			class="px-1.5 py-1 w-full rounded-md flex items-start"
			:class="[active ? 'bg-gray-100 ' : '']"
		>
			<!-- Icon  -->
			<div class="mt-0.5 mr-2">
				<component
					:is="icon"
					class="w-3.5 h-3.5 shrink-0 text-gray-600"
					stroke-width="2"
				/>
			</div>

			<!-- Assistant and LLM name -->
			<div class="w-full">
				<p class="w-full text-gray-900 font-medium text-base mb-0.5 text-nowrap text-left">
					{{ title }}
				</p>
				<p class="text-sm text-gray-600 text-left text-nowrap">
					{{ description }}
				</p>
			</div>

			<!-- Selected Check -->
			<div v-if="selected" class="ml-auto my-auto">
				<Check class="w-3.5 h-3.5 shrink-0 text-gray-700" stroke-width="2" />
			</div>
		</div>
	</button>
</template>
<script setup lang="ts">
import type { Component } from "vue";
import { Check } from "lucide-vue-next";

withDefaults(
	defineProps<{
		title: string;
		icon: Component;
		description: string;
		selected?: boolean;
		active?: boolean;
	}>(),
	{
		selected: false,
		active: false,
	}
);
</script>
