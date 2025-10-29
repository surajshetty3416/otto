<template>
	<template v-for="(message, i) in messages" :key="message.id">
		<UserMessage
			v-if="message.meta.role === 'user'"
			:message="message"
			class="ml-auto"
			:class="{ 'mb-8': messages[i + 1]?.meta.role === 'agent' }"
		/>
		<AgentMessage
			v-if="message.meta.role === 'agent'"
			:message="message"
			:class="{ 'mb-8': messages[i + 1]?.meta.role === 'user' }"
		/>
	</template>
</template>

<script setup lang="ts">
import type { SessionItem } from "@/client/generated.types";
import AgentMessage from "./AgentMessage.vue";
import UserMessage from "./UserMessage.vue";

defineProps<{
	messages: SessionItem[];
}>();
</script>
