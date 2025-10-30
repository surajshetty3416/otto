<template>
	<div class="w-1 h-1 bg-gray-300 rounded-full" :class="`bg-${color}-400`"></div>
</template>
<script setup lang="ts">
type Color = "gray" | "yellow" | "green" | "red";
withDefaults(defineProps<{ color: Color }>(), { color: "gray" });
</script>
