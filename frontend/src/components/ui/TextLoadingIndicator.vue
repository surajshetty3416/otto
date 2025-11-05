<template>
	<div class="flex items-center gap-1">
		<LoadingIndicator class="w-3 h-3 text-gray-500" />
		<p class="text-sm font-medium text-gray-500">
			<Ellipsis>{{ text }}</Ellipsis>
		</p>
	</div>
</template>

<script setup lang="ts">
import LoadingIndicator from "../fui/LoadingIndicator.vue";
import Ellipsis from "./Ellipsis.vue";

defineProps<{ text: string }>();
</script>
