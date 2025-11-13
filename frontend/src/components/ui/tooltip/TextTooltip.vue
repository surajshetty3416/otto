<template>
	<Tooltip
		v-bind="$attrs"
		:disabled="disabled"
		:delay="delay"
		:side="side"
		:align="align"
		:skipDelay="skipDelay"
		:alignOffset="alignOffset"
		:sideOffset="sideOffset"
	>
		<slot />
		<template #content>
			<p class="px-2 py-2 text-gray-800 text-sm">{{ content }}</p>
			<kbd v-if="keybind" class="px-2 pb-1 pt-0.5 flex justify-end gap-1">
				<span
					v-for="key in keybind"
					:key="key"
					class="px-1 rounded-sm bg-gray-200 text-gray-700 text-sm mt-1"
					>{{ key }}</span
				>
			</kbd>
		</template>
	</Tooltip>
</template>

<script setup lang="ts">
import { computed } from "vue";
import Tooltip from "./Tooltip.vue";
import { isMacOS } from "@/utils";

defineOptions({
	inheritAttrs: false,
});

const props = withDefaults(
	defineProps<{
		content: string;
		keybinds?: string | string[];
		disabled?: boolean;
		delay?: number;
		side?: "top" | "bottom" | "left" | "right";
		align?: "start" | "center" | "end";
		skipDelay?: boolean;
		alignOffset?: number;
		sideOffset?: number;
	}>(),
	{
		disabled: false,
		delay: 100,
		side: "top",
		align: "center",
		skipDelay: false,
	}
);

const keybind = computed(() => {
	if (!props.keybinds || props.keybinds.length === 0) return null;

	const k = Array.isArray(props.keybinds) ? props.keybinds[0] : props.keybinds;
	const keys = k.split("+");
	const list = [];
	for (const key of keys) {
		if (key.length === 1) list.push(key.toUpperCase());
		if (key.startsWith("key")) list.push(key.slice(3).toUpperCase());
		else if (isMacOS)
			list.push(
				key
					.replace("meta", "⌘")
					.replace("control", "⌃")
					.replace("alt", "⌥")
					.replace("backspace", "delete")
			);
		else
			list.push(
				key
					.replace("control", "Ctrl")
					.replace("shift", "Shift")
					.replace("alt", "Alt")
					.replace("win", "Win")
			);
	}

	return list;
});
</script>
