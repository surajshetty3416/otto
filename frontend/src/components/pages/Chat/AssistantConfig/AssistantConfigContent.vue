<template>
	<div class="flex-1 overflow-y-auto px-4">
		<pre class="text-xs">{{ assistant }}</pre>
	</div>
</template>
<script lang="ts" setup>
import type { Assistant } from "@/client/generated.types";

defineProps<{ assistant: Assistant }>();
</script>
