<template>
	<div
		v-if="message"
		class="whitespace-pre-line text-sm text-ink-red-4"
		role="alert"
		v-html="message ?? ''"
	></div>
</template>

<script setup lang="ts">
defineProps<{
	message?: string;
}>();
</script>
