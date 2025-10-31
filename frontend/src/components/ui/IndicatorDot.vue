<template>
	<div
		class="w-1 h-1 rounded-full shrink-0"
		:class="{
			'bg-gray-400': color === 'gray',
			'bg-orange-400': color === 'orange',
			'bg-yellow-400': color === 'yellow',
			'bg-green-400': color === 'green',
			'bg-red-400': color === 'red',
		}"
	></div>
</template>
<script setup lang="ts">
type Color = "gray" | "yellow" | "green" | "red" | "orange";
withDefaults(defineProps<{ color: Color }>(), { color: "gray" });
</script>
