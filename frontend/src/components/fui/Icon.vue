<template>
	<!-- @vue-expect-error -->
	<component
		:is="icon"
		:size="size"
		:color="color"
		:stroke-width="strokeWidth"
		:default-class="defaultClass"
	/>
</template>

<script setup lang="ts">
import { computed } from "vue";
import * as icons from "lucide-vue-next";
import type { IconName } from "./types";

const props = defineProps<{
	name: IconName;
	size?: number;
	color?: string;
	strokeWidth?: number;
	defaultClass?: string;
}>();

const icon = computed(() => icons[props.name as IconName]);
</script>
