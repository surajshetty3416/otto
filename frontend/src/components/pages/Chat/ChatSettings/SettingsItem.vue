<template>
	<div>
		<div class="flex items-center justify-between gap-2">
			<label
				for="tool_permissions"
				class="text-base font-medium text-gray-900 flex items-center gap-2"
			>
				<component
					v-if="icon"
					:is="icon"
					class="w-3.5 h-3.5 text-gray-700"
					stroke-width="1.5"
				/>
				{{ label }}
			</label>
			<slot />
		</div>
		<p v-if="description" class="text-sm text-gray-500 mt-1" :class="[icon ? 'ml-5.5' : 'ml-0']">
			{{ description }}
		</p>
	</div>
</template>
<script lang="ts" setup>
import type { Component } from "vue";

defineProps<{
	label: string;
	icon?: Component;
	description?: string;
}>();
</script>
