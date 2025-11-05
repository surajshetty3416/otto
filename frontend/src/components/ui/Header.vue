<template>
	<div
		ref="headerRef"
		class="h-14 w-full transition-all duration-200 border-b glass-lg shrink-0"
		:class="isScrolled ? 'border-gray-200' : 'border-white'"
	>
		<slot />
	</div>
</template>
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

const headerRef = ref<HTMLElement | null>(null);
const isScrolled = ref(false);

function handleScroll(event: Event) {
	const target = event.target as HTMLElement;
	isScrolled.value = target.scrollTop > 0;
}

onMounted(() => {
	if (!headerRef.value) return;

	const scrollContainer = headerRef.value.nextElementSibling as HTMLElement;
	if (scrollContainer) {
		scrollContainer.addEventListener("scroll", handleScroll);
	}
});

onUnmounted(() => {
	if (!headerRef.value) return;

	const scrollContainer = headerRef.value.nextElementSibling as HTMLElement;
	if (scrollContainer) {
		scrollContainer.removeEventListener("scroll", handleScroll);
	}
});
</script>
