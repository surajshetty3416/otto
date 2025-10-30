<template>
	<button
		:disabled="disabled || loading"
		class="flex items-center justify-center text-sm"
		:class="{
			'rounded-sm px-1 py-0.5': !rounded,
			'rounded-full p-0.5': rounded,
			'text-gray-600': !isPrimary,
			'bg-gray-300 text-gray-700': !!isPrimary,
			'opacity-50 cursor-not-allowed': disabled,
			'opacity-75 cursor-progress': loading,
			'hover:bg-gray-200': !isPrimary && !(loading || disabled),
			'hover:bg-gray-400': isPrimary && !(loading || disabled),
		}"
	>
		<slot />
	</button>
</template>

<script setup lang="ts">
withDefaults(
	defineProps<{
		isPrimary?: boolean;
		disabled?: boolean;
		loading?: boolean;
		rounded?: boolean;
	}>(),
	{
		isPrimary: false,
		disabled: false,
		loading: false,
		rounded: false,
	}
);
</script>
