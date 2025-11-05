<template>
	<TooltipProvider
		:delayDuration="delay"
		:disabled="disabled"
		:skipDelayDuration="skipDelay ? 0 : 300"
	>
		<TooltipBase>
			<TooltipTrigger v-bind="$attrs">
				<slot />
			</TooltipTrigger>
			<TooltipContent
				:side="side"
				:align="align"
				:alignOffset="alignOffset"
				:sideOffset="sideOffset"
				class="bg-white border border-gray-200 shadow-sm p-0"
			>
				<slot name="content" />
			</TooltipContent>
		</TooltipBase>
	</TooltipProvider>
</template>

<script setup lang="ts">
import {
	TooltipBase,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from "@/components/ui/tooltip";

defineOptions({
	inheritAttrs: false,
});

withDefaults(
	defineProps<{
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
		delay: 200,
		side: "top",
		align: "center",
		skipDelay: false,
	}
);
</script>
