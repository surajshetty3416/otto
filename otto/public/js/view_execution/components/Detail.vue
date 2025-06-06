<script setup>
// import { link_icon } from "../utils";
import Link from "./Link.vue";

const props = defineProps({
	label: { type: String, required: true },
	value: { type: String, required: true },
	link: { type: String, required: false },
});
</script>

<template>
	<div class="detail">
		<label>{{ label }}</label>
		<Link class="link" v-if="link" :link="link">{{ value }}</Link>
		<p v-else>{{ value }}</p>
	</div>
</template>

<style scoped>
.detail {
	label {
		font-size: var(--text-xs);
		color: var(--gray-500);
		margin: 0;
		padding: 0;
		/* margin-bottom: var(--padding-xs); */
	}

	p,
	.link {
		color: var(--gray-800);
		font-size: var(--text-md);
		margin: 0;
		padding: 0;
	}
}
</style>
