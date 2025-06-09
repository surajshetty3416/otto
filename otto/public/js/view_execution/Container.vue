<script setup>
import ViewExecution from "./ViewExecution.vue";

const props = defineProps({
	executionName: {
		type: String,
		required: true,
	},
});
</script>
<template>
	<div class="container">
		<ViewExecution :execution-name="executionName" />
	</div>
</template>

<style scoped>
.container {
	border-left: 1px solid var(--gray-200);
	border-right: 1px solid var(--gray-200);
	width: 70vw;
	margin: 0 auto;
	padding: 0;
	border-radius: 0;
	border-top: none;
	border-bottom: none;
}
</style>
