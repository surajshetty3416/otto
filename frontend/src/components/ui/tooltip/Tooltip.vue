<template>
	<TooltipProvider :delayDuration="delay">
		<TooltipBase>
			<TooltipTrigger v-bind="$attrs">
				<slot />
			</TooltipTrigger>
			<TooltipContent
				:side="side"
				:align="align"
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
		delay?: number;
		side?: "top" | "bottom" | "left" | "right";
		align?: "start" | "center" | "end";
	}>(),
	{
		delay: 200,
		side: "top",
		align: "center",
	}
);
</script>
