<template>
	<Combobox
		v-bind="$attrs"
		v-model="modelValue"
		v-model:search="search"
		:options="options"
		:loading="linkOptions.loading.value"
		:show-search="true"
	>
		<template v-slot="{ options, select, cursor }">
			<slot :options="options" :select="select" :cursor="cursor"></slot>
		</template>
	</Combobox>
</template>

<script setup lang="ts">
import { smartMatch } from "@/utils";
import { computed, ref } from "vue";
import Combobox from "../combobox/Combobox.vue";
import type { LinkProps } from "./types";
import { useLinkOptions } from "./utils";

const search = ref("");
const props = defineProps<LinkProps>();

// @ts-expect-error - not possible to reasonably type the fieldname
const linkOptions = useLinkOptions(props.doctype, props.fieldname, props.fields);
const modelValue = defineModel<string | null>({ required: true });
const transformed = computed(() => {
	if (props.transform) return linkOptions.options.map(props.transform);
	return linkOptions.options;
});

const options = computed(() => {
	let _options = transformed.value;
	if (search.value) {
		_options = _options.filter((option) => smartMatch(option.label, search.value));
	}

	if (search.value && _options.length < 10 && !linkOptions.isEnd.value) {
		linkOptions.next();
	}

	return _options;
});
</script>
