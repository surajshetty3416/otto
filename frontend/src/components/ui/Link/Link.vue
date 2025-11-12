<template>
	<div class="relative flex items-center" :class="containerClass">
		<div
			:class="['absolute inset-y-0 left-0 flex items-center', textColor, prefixClasses]"
			v-if="$slots.prefix"
		>
			<slot name="prefix"> </slot>
		</div>
		<div
			v-if="placeholder"
			v-show="!modelValue"
			class="pointer-events-none absolute text-ink-gray-4 truncate w-full"
			:class="[fontSizeClasses, paddingClasses, $slots.prefix ? 'pl-8' : '']"
		>
			{{ placeholder }}
		</div>
		<select
			:class="[selectClasses, $slots.prefix ? 'pl-8' : '']"
			:disabled="disabled"
			:id="id"
			v-model="modelValue"
			v-bind="attrs"
		>
			<option
				v-for="option in options"
				:key="option.value"
				:value="option.value"
				:disabled="option.disabled || false"
				:selected="modelValue === option.value"
			>
				{{ option.label }}
			</option>
		</select>
	</div>
</template>

<script setup lang="ts">
import { computed, useAttrs } from "vue";
import type { LinkProps } from "./types";
import { useLinkOptions } from "./utils";

defineOptions({
	inheritAttrs: false,
});

const props = withDefaults(defineProps<LinkProps>(), {
	size: "sm",
	variant: "subtle",
});

// @ts-expect-error - not possible to reasonably type the fieldname
const linkOptions = useLinkOptions(props.doctype, props.fieldname, props.fields);
const attrs = useAttrs();
const modelValue = defineModel<string | null>({ required: true });

const options = computed(() => {
	let _options = linkOptions.options;
	if (props.transform) {
		_options = _options.map(props.transform);
	}
	return _options;
});

const textColor = computed(() => {
	return props.disabled ? "text-ink-gray-4" : "text-ink-gray-8";
});

const fontSizeClasses = computed(() => {
	return {
		xs: "text-sm",
		sm: "text-base",
		md: "text-base",
		lg: "text-lg",
		xl: "text-xl",
	}[props.size];
});

const paddingClasses = computed(() => {
	return {
		xs: "pl-2 pr-5",
		sm: "pl-2 pr-5",
		md: "pl-2.5 pr-5.5",
		lg: "pl-3 pr-6",
		xl: "pl-3 pr-6",
	}[props.size];
});

const selectClasses = computed(() => {
	let sizeClasses = {
		xs: "rounded-md h-6",
		sm: "rounded h-7",
		md: "rounded h-8",
		lg: "rounded-md h-10",
		xl: "rounded-md h-10",
	}[props.size];

	let variant = props.disabled ? "disabled" : props.variant;
	let variantClasses = {
		subtle: "border border-[--surface-gray-2] bg-surface-gray-2 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3",
		outline:
			"border border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3",
		ghost: "bg-transparent border-transparent hover:bg-surface-gray-3 focus:bg-surface-gray-3 focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3",
		disabled: [
			"border",
			props.variant !== "ghost" ? "bg-surface-gray-1" : "",
			props.variant === "outline" ? "border-outline-gray-2" : "border-transparent",
		],
	}[variant];

	return [
		sizeClasses,
		fontSizeClasses.value,
		paddingClasses.value,
		variantClasses,
		textColor.value,
		"transition-colors w-full py-0 truncate",
	];
});

let prefixClasses = computed(() => {
	return {
		xs: "pl-1.5",
		sm: "pl-2",
		md: "pl-2.5",
		lg: "pl-3",
		xl: "pl-3",
	}[props.size];
});
</script>
