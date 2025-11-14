<template>
	<template v-for="(message, i) in messages" :key="message.id">
		<UserMessage
			v-if="message.meta.role === 'user'"
			:message="message"
			class="user-message ml-auto"
			:class="{
				'mb-12': messages[i + 1]?.meta.role === 'agent',
				'mt-12': messages[i - 1]?.meta.role === 'agent',
			}"
			style="max-width: 85%"
		/>

		<!-- 
		Assistant Messages

		This is not a separate component cause some of the content types toggle
		between inline and block elements. When inline, we want all inline elements
		to show on the same line.

		If wrapped in a div this is more tedious to manage across multiple assistant
		messages and one has to resort to js to decide whether the wrapper div
		should be inline or block.
		-->
		<template v-if="message.meta.role === 'agent'">
			<template v-for="(content, j) in message.content" :key="j">
				<TextContent v-if="content.type === 'text'" :item="message" :content="content" />
				<ThinkingContent
					v-if="content.type === 'thinking'"
					:item="message"
					:content="content"
				/>
				<ToolUseContent
					v-if="content.type === 'tool_use'"
					:item="message"
					:content="content"
				/>
			</template>
		</template>
	</template>
	<div class="expander-div shrink-0"></div>
</template>

<script setup lang="ts">
import type { SessionItem } from "@/client/generated.types";
import TextContent from "./TextContent.vue";
import ThinkingContent from "./ThinkingContent.vue";
import ToolUseContent from "./ToolUseContent.vue";
import UserMessage from "./UserMessage.vue";

defineProps<{ messages: SessionItem[] }>();
</script>
