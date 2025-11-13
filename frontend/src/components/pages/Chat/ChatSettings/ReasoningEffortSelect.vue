<template>
	<Select
		doctype="Otto Chat"
		fieldname="reasoning_effort"
		placeholder="Select effort"
		v-model="modelValue"
		size="xs"
		variant="ghost"
		:disabled="disabled"
	>
		<template #trigger>
			<slot name="trigger"></slot>
		</template>
	</Select>
</template>

<script setup lang="ts">
import Select from "@/components/ui/Select/Select.vue";

const modelValue = defineModel<string | null>({ required: true });

defineProps<{
	disabled?: boolean;
}>();
</script>

