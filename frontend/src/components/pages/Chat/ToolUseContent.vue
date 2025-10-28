<template>
	<div>
		<p>{{ content.name }}</p>
		<pre>{{ content.args }}</pre>
	</div>
</template>
<script setup lang="ts">
import type { ToolUseContent } from "@/client/generated.types";

/**
 * show a pill with tool name (?) to indicate a tool use on clicking the pill
 * expand dialog to show tool use details (args, result, stdout, stderr,
 * permission, etc)
 * 
 * show a semi-collapsed div (hide args) when permission request is required
 * pill is inline, i.e. multiple tool calls should be shown in a row
 * full width is when user clicks the i button
 */

defineProps<{
	content: ToolUseContent;
}>();
</script>
