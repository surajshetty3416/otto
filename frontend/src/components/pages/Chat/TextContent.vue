<template>
	<pre class="text-sm overflow-auto">{{ content.text }}</pre>
</template>
<script setup lang="ts">
import type { TextContent } from "@/client/generated.types";

// TODO: render markdown if agent else syntax highlight as markdown if user
defineProps<{
	content: TextContent;
}>();
</script>
