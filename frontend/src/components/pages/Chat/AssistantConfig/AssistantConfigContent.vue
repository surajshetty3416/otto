<template>
	<div class="flex-1 overflow-y-auto px-4">
		<TextLoadingIndicator v-if="get_assistant_details.loading" text="Loading details" />
		<pre class="text-xs text-wrap" v-else>{{ get_assistant_details.data }}</pre>
	</div>
</template>
<script lang="ts" setup>
import { api } from "@/client";
import type { Assistant } from "@/client/generated.types";
import TextLoadingIndicator from "@/components/ui/TextLoadingIndicator.vue";
import { watch } from "vue";

const props = defineProps<{ assistant: Assistant }>();
const get_assistant_details = api.chat.get_assistant_details(
	{ name: props.assistant.name },
	{ cache: true }
);
watch(
	() => props.assistant.name,
	() => get_assistant_details.run({ name: props.assistant.name }, false)
);
</script>
