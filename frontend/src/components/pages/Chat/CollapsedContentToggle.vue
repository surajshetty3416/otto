<template>
	<div class="inline-block rounded-full mr-1.5 mb-3">
		<button
			@click="$emit('update:modelValue', !modelValue)"
			class="bg-gray-50 border border-gray-200 py-1.5 px-1.5 w-fit rounded-full flex items-center gap-1.5"
			:class="modelValue ? 'ring-1 ring-gray-400 border-gray-400' : 'border-gray-200'"
		>
			<slot />
		</button>
	</div>
</template>
<script setup lang="ts">
defineProps<{
	modelValue: boolean;
}>();
</script>
