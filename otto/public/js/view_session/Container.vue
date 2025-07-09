<script setup>
import ViewSession from "./ViewSession.vue";
import { computed } from "vue";

const props = defineProps({
	session: {
		type: String,
		required: true,
	},
	// sessions: {
	// 	type: Array,
	// 	required: true,
	// },
});
</script>
<template>
	<div class="container">
		<!-- <template v-for="session in sessions" :key="session">
			<ViewSession :session-name="session" />
		</template> -->
		<ViewSession v-if="session" :session-name="session" />
	</div>
</template>

<style scoped>
.container {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(calc(100vw / 3 - 1rem), 1fr));
	gap: 1rem;
	max-width: 100vw;
	margin: 0 auto;
}

@media (min-width: 768px) {
	.container {
		max-width: 720px;
	}
}

@media (min-width: 992px) {
	.container {
		max-width: 960px;
	}
}

@media (min-width: 1200px) {
	.container {
		max-width: 1140px;
	}
}

.session-viewer {
	width: 100%;
	border-left: 1px solid var(--gray-200);
	border-right: 1px solid var(--gray-200);
	margin: 0 auto;
	padding: 0;
	border-radius: 0;
	border-top: none;
	border-bottom: none;
}
</style>
