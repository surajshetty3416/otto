<script setup>
import { link_icon } from "../utils";

const props = defineProps({
	label: { type: String, required: true },
	value: { type: String, required: true },
	link: { type: String, required: false },
});
</script>

<template>
	<div class="detail">
		<label>{{ label }}</label>
		<a v-if="link" :href="link" target="_blank">
			<p>
				{{ value }}
			</p>
			<div v-html="link_icon" />
		</a>
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

	p {
		color: var(--gray-800);
		font-size: var(--text-md);
		margin: 0;
		padding: 0;
	}

	a {
		display: flex;
		align-items: center;
		gap: var(--padding-sm);
	}

	a:hover {
		p {
			color: var(--gray-900);
		}
		text-decoration: none;
	}
}
</style>
