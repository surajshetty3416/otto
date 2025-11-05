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
			<p class="px-2 py-1 text-gray-700 text-sm">{{ content }}</p>
		</template>
	</Tooltip>
</template>

<script setup lang="ts">
import Tooltip from "./Tooltip.vue";

defineOptions({
	inheritAttrs: false,
});

withDefaults(
	defineProps<{
		content: string;
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
</script>
