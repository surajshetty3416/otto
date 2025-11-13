<template>
	<Combobox
		v-bind="$attrs"
		v-model="modelValue"
		:options="selectOptions"
		:loading="false"
		:show-search="false"
	>
		<template #trigger>
			<slot name="trigger"></slot>
		</template>
		<template v-slot="{ options, select, cursor }">
			<slot :options="options" :select="select" :cursor="cursor"></slot>
		</template>
	</Combobox>
</template>

<script setup lang="ts">
import { useMeta } from "@/components/utils";
import { computed } from "vue";
import Combobox from "../combobox/Combobox.vue";
import type { ComboboxOption } from "../combobox/types";
import type { SelectProps } from "./types";

const props = defineProps<SelectProps>();
const meta = useMeta(props.doctype, props.fieldname);
const modelValue = defineModel<string | null>({ required: true });

const selectOptions = computed(() => {
	if (meta.value?.options) {
		return meta.value.options.split("\n").map((option) => {
			return {
				label: option,
				value: option,
			} as ComboboxOption;
		});
	}

	return (
		props.options
			?.map((option) => {
				if (typeof option === "string") {
					return {
						label: option,
						value: option,
					};
				}
				return option;
			})
			.filter(Boolean) || []
	);
});
</script>
