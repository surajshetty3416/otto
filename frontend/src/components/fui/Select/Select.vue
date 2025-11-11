<template>
	<div class="flex flex-col gap-1.5">
		<div v-if="label" class="text-sm font-medium text-gray-700">{{ label }}</div>
		<div class="relative flex items-center">
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
					v-for="option in selectOptions"
					:key="option.value"
					:value="option.value"
					:disabled="option.disabled || false"
					:selected="modelValue === option.value"
				>
					{{ option.label }}
				</option>
			</select>
		</div>
		<div v-if="description" class="text-sm text-ink-gray-4">
			<p v-html="description"></p>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useMeta } from "@/components/utils";
import { computed, useAttrs } from "vue";
import type { SelectProps } from "./types";

defineOptions({
	inheritAttrs: false,
});

const props = withDefaults(defineProps<SelectProps>(), {
	size: "sm",
	variant: "subtle",
});
const meta = useMeta(props.doctype, props.fieldname);

const attrs = useAttrs();
const modelValue = defineModel<string | null>({ required: true });

const selectOptions = computed(() => {
	if (meta.value?.options) {
		return meta.value.options.split("\n").map((option) => {
			return {
				label: option,
				value: option,
				disabled: false,
			};
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

const label = computed(() => {
	if (props.label) return props.label;
	if (props.showLabel) return meta.value?.label;
	return null;
});

const description = computed(() => {
	if (props.description) return props.description;
	if (props.showDescription) return meta.value?.description;
	return null;
});

const textColor = computed(() => {
	return props.disabled ? "text-ink-gray-4" : "text-ink-gray-8";
});

const fontSizeClasses = computed(() => {
	return {
		sm: "text-base",
		md: "text-base",
		lg: "text-lg",
		xl: "text-xl",
	}[props.size];
});

const paddingClasses = computed(() => {
	return {
		sm: "pl-2 pr-5",
		md: "pl-2.5 pr-5.5",
		lg: "pl-3 pr-6",
		xl: "pl-3 pr-6",
	}[props.size];
});

const selectClasses = computed(() => {
	let sizeClasses = {
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
		sm: "pl-2",
		md: "pl-2.5",
		lg: "pl-3",
		xl: "pl-3",
	}[props.size];
});
</script>
