<template>
	<div>
		<p class="text-gray-800 text-4xl font-medium">{{ message }}</p>
	</div>
</template>
<script lang="ts" setup>
import { computed } from "vue";

const messages = [
	"Hi there!",
	"What can I help you with?",
	"What would you like to do today?",
	"What would you like to get done today?",
	"How can I help you today?",
];

const message = computed(() => {
	return messages[Math.floor(Math.random() * messages.length)];
});
</script>
