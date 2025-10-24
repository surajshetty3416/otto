<template>
	<div>
		<div v-for="message in messages" :key="message.id">
			<pre>{{ message.content }}</pre>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { SessionItem } from "@/client/generated.types";

const props = defineProps<{
	messages: SessionItem[];
}>();
</script>
