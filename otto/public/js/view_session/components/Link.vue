<script setup>
import { link_icon } from "../utils";
const props = defineProps({
	// value: { type: String, required: true },
	link: { type: String, required: false },
});
</script>

<template>
	<a v-if="link" :href="link" target="_blank" class="link">
		<p>
			<slot></slot>
		</p>
		<span v-html="link_icon" />
	</a>
</template>

<style scoped>
.link {
	display: flex;
	align-items: center;
	gap: var(--padding-sm);

	p {
		margin: 0;
		padding: 0;
	}
}

.link:hover {
	p {
		color: var(--gray-900);
	}
	text-decoration: none;
}
</style>
