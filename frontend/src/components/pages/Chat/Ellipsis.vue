<template>
	<span>
		<slot />

		<span style="width: 1.5ch; display: inline-block">
			{{ dots }}
		</span>
	</span>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";

const dots = ref("");
let interval = null;

onMounted(() => {
	interval = setInterval(() => {
		dots.value = ".".repeat((dots.value.length + 1) % 4);
	}, 500);
});

onBeforeUnmount(() => clearInterval(interval));
</script>
