<template>
	<TextTooltip
		:content="item.name"
		side="right"
		align="center"
		:delay="0"
		:skipDelay="true"
		:sideOffset="-4"
		:disabled="!!textOpacity"
	>
		<component
			:is="item.route ? 'router-link' : 'a'"
			:to="item.route"
			:href="item.href"
			class="flex items-center rounded-md hover:bg-gray-50 cursor-pointer p-2 mx-2 overflow-hidden"
			:class="{ 'bg-gray-100': isActive }"
		>
			<!-- Icon -->
			<div class="shrink-0 text-gray-700">
				<component :is="item.icon" class="w-4.5 h-4.5" strokeWidth="1.5" />
			</div>

			<!--  Label -->
			<p
				class="text-base font-medium text-gray-800 whitespace-nowrap transition-opacity duration-200 ml-2"
				:style="{ opacity: textOpacity }"
			>
				{{ item.name }}
			</p>
		</component>
	</TextTooltip>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { SidebarItem } from "./types";
import router from "@/router";
import TextTooltip from "../tooltip/TextTooltip.vue";

const props = defineProps<{
	item: SidebarItem;
	textOpacity: number;
}>();

const isActive = computed(() => {
	console.log(props.item.route, router.currentRoute.value);
	if (!props.item.route) return false;

	return router.currentRoute.value.path.startsWith(props.item.route);
});
</script>
