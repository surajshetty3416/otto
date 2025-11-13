<template>
	<div
		class="relative border-r border-gray-200 shrink-0 h-screen flex flex-col transition-all duration-300 ease-in-out bg-gray-25"
		:style="{ width: `${sidebarWidth}px` }"
	>
		<!-- Header with Logo and Collapse Toggle -->
		<div class="flex items-center justify-between p-4 border-gray-200 mb-4 shrink-0">
			<div
				:class="{ 'cursor-pointer': isCollapsed }"
				@click="isCollapsed ? toggleCollapse() : null"
			>
				<LogoThickLine class="flex-shrink-0 w-4.5 h-4.5" />
			</div>

			<TextTooltip
				content="Toggle sidebar"
				:keybinds="keybinds['toggle-sidebar']"
				:delay="500"
			>
				<button @click="toggleCollapse" class="flex-shrink-0 bg-transparent z-0">
					<ArrowLeftToLine
						class="w-4 h-4 text-gray-600 transition-all duration-150"
						:style="{ opacity: textOpacity }"
						:class="{ 'rotate-180': isCollapsed }"
						stroke-width="1.5"
					/></button
			></TextTooltip>
		</div>

		<!-- Navigation Items -->
		<nav class="flex flex-col shrink-0">
			<SidebarItem
				class="shrink-0"
				v-for="item in navigationItems"
				:key="item.name"
				:item="item"
				:text-opacity="textOpacity"
			/>
		</nav>

		<!-- Chat List -->
		<ChatList
			class="mt-8 mx-2 flex-1 overflow-y-auto overflow-x-hidden transition-all duration-200"
			:class="{ 'opacity-0': isCollapsed }"
		/>

		<!-- Footer -->
		<SidebarFooter class="p-4 shrink-0" :is-collapsed="isCollapsed" />
	</div>
</template>

<script setup lang="ts">
import LogoThickLine from "@/components/svg/LogoThickLine.vue";
import { ArrowLeftToLine, Bot, ClipboardList, MessageSquare, Wrench } from "lucide-vue-next";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import ChatList from "./ChatList.vue";
import SidebarFooter from "./SidebarFooter.vue";
import SidebarItem from "./SidebarItem.vue";
import type { SidebarItem as SidebarItemType } from "./types";
import { sidebarState } from "./utils";
import shortcuts, { keybinds } from "@/shortcuts";
import TextTooltip from "../tooltip/TextTooltip.vue";

// Sidebar width management
const DEFAULT_WIDTH = 256;
const COLLAPSED_WIDTH = 20 + 16 * 2;

const isCollapsed = ref(sidebarState.get("isCollapsed") ?? false);
watch(isCollapsed, (newVal) => sidebarState.set("isCollapsed", newVal));
const sidebarWidth = ref(isCollapsed.value ? COLLAPSED_WIDTH : DEFAULT_WIDTH);

// Calculate text opacity based on width
const textOpacity = computed(() => {
	if (sidebarWidth.value <= COLLAPSED_WIDTH) return 0;
	return (sidebarWidth.value - COLLAPSED_WIDTH) / (DEFAULT_WIDTH - COLLAPSED_WIDTH);
});

// Navigation items
const navigationItems: SidebarItemType[] = [
	{
		name: "Chat",
		icon: MessageSquare,
		route: "/chat",
	},
	{
		name: "Assistants",
		icon: Bot,
		href: "/app/otto-assistant",
	},
	{
		name: "Tools",
		icon: Wrench,
		href: "/app/otto-tool",
	},
	{
		name: "Tasks",
		icon: ClipboardList,
		href: "/app/otto-task",
	},
];

function toggleCollapse(e?: KeyboardEvent | MouseEvent) {
	e?.preventDefault();
	e?.stopPropagation();

	isCollapsed.value = !isCollapsed.value;
	sidebarWidth.value = isCollapsed.value ? COLLAPSED_WIDTH : DEFAULT_WIDTH;
}

onMounted(() => {
	shortcuts.on("toggle-sidebar", toggleCollapse);
});

onUnmounted(() => {
	shortcuts.off("toggle-sidebar", toggleCollapse);
});
</script>
