<template>
	<div class="flex flex-col gap-8">
		<template v-for="message in messages" :key="message.id">
			<UserMessage v-if="message.meta.role === 'user'" :message="message" class="ml-auto" />
			<AgentMessage v-if="message.meta.role === 'agent'" :message="message" />
		</template>
	</div>
</template>

<script setup lang="ts">
import type { SessionItem } from "@/client/generated.types";
import AgentMessage from "./AgentMessage.vue";
import UserMessage from "./UserMessage.vue";

defineProps<{
	messages: SessionItem[];
}>();
</script>
