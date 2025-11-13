<template>
	<Select
		doctype="Otto Chat"
		fieldname="tool_permissions"
		placeholder="Select option"
		v-model="modelValue"
		size="xs"
		variant="ghost"
	>
		<template #trigger>
			<slot name="trigger"></slot>
		</template>
	</Select>
</template>

<script setup lang="ts">
import Select from "@/components/ui/Select/Select.vue";

const modelValue = defineModel<string | null>({ required: true });
</script>

