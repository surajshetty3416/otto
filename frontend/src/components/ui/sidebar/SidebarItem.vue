<template>
	<component
		:is="item.route ? 'router-link' : 'a'"
		:to="item.route"
		:href="item.href"
		class="flex items-center rounded-md hover:bg-gray-100 cursor-pointer p-2 mx-2 overflow-hidden"
	>
		<!-- Icon -->
		<div class="shrink-0 text-gray-800">
			<component :is="item.icon" class="w-4.5 h-4.5" strokeWidth="1.5" />
		</div>

		<!--  Label -->
		<p
			class="text-base font-medium text-gray-900 whitespace-nowrap transition-opacity duration-200 ml-2"
			:style="{ opacity: textOpacity }"
		>
			{{ item.name }}
		</p>
	</component>
</template>

<script setup lang="ts">
import type { SidebarItem } from "./types";

defineProps<{
	item: SidebarItem;
	textOpacity: number;
}>();
</script>
