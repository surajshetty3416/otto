<template>
	<div>
		<template v-for="(content, i) in message.content" :key="i">
			<TextContent v-if="content.type === 'text'" :content="content" />
			<ThinkingContent v-if="content.type === 'thinking'" :content="content" />
			<ToolUseContent v-if="content.type === 'tool_use'" :content="content" />
		</template>
	</div>
</template>
<script setup lang="ts">
import type { SessionItem } from "@/client/generated.types";
import { provide } from "vue";
import TextContent from "./TextContent.vue";
import ThinkingContent from "./ThinkingContent.vue";
import ToolUseContent from "./ToolUseContent.vue";
import { sessionItemKey } from "./utils";

const props = defineProps<{
	message: SessionItem;
}>();

provide(sessionItemKey, props.message);
</script>
