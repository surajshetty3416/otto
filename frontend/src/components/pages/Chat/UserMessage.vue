<template>
	<div class="bg-gray-200 py-2 px-4 w-fit rounded-md">
		<template v-for="(content, i) in message.content" :key="i">
			<p v-if="content.type === 'text'">{{ content.text }}</p>
		</template>
	</div>
</template>
<script setup lang="ts">
import type { SessionItem } from "@/client/generated.types";
import { provide } from "vue";
import { sessionItemKey } from "./utils";
const props = defineProps<{
	message: SessionItem;
}>();

provide(sessionItemKey, props.message);
</script>
