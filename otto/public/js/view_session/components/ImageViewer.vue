<script setup>
import { ref } from "vue";
import ContentSectionHeader from "./ContentSectionHeader.vue";

const props = defineProps({
	index: { type: Number, required: true },
	content: { type: Object, required: true },
});

const show = ref(false);
</script>
<template>
	<div>
		<!-- Header -->
		<ContentSectionHeader v-model="show" :index="index" label="Image" />

		<!-- Image -->
		<div v-if="show" class="content">
			<img :src="content.url || content.data" alt="image content" class="image-content" />
		</div>
	</div>
</template>
<style scoped>
.content {
	display: flex;
	justify-content: center;
	align-items: center;
	padding: var(--padding-sm);
	border: 1px solid var(--gray-200);

	img {
		max-width: 100%;
		max-height: 100%;
	}
}
</style>
