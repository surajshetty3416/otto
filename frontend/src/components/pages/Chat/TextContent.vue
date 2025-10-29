<template>
	<Markdown style="font-size: 100%;">{{ content.text }}</Markdown>
</template>
<script setup lang="ts">
import type { TextContent } from "@/client/generated.types";
import Markdown from "./Markdown.vue";

defineProps<{
	content: TextContent;
}>();
</script>
