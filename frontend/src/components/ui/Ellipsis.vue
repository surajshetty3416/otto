<template>
	<span>
		<slot />

		<span style="width: 1.5ch; display: inline-block">
			{{ dots }}
		</span>
	</span>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";

const dots = ref("");
let timeout: NodeJS.Timeout | null = null;

onMounted(() => {
	timeout = setInterval(() => {
		dots.value = ".".repeat((dots.value.length + 1) % 4);
	}, 300);
});

onBeforeUnmount(() => timeout && clearInterval(timeout));
</script>
