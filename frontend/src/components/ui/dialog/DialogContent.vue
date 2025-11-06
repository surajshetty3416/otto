<script setup lang="ts">
import type { DialogContentEmits, DialogContentProps } from "reka-ui";
import type { HTMLAttributes } from "vue";
import { reactiveOmit } from "@vueuse/core";
import { X } from "lucide-vue-next";
import {
	DialogClose,
	DialogContent,
	DialogOverlay,
	DialogPortal,
	useForwardPropsEmits,
} from "reka-ui";
import { cn } from "@/lib/utils";

const props = withDefaults(
	defineProps<DialogContentProps & { class?: HTMLAttributes["class"]; noHeader?: boolean }>(),
	{
		noHeader: false,
	}
);
const emits = defineEmits<DialogContentEmits>();

const delegatedProps = reactiveOmit(props, "class");

const forwarded = useForwardPropsEmits(delegatedProps, emits);
</script>

<template>
	<DialogPortal>
		<DialogOverlay
			class="fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
		/>
		<DialogContent
			v-bind="forwarded"
			:class="
				cn(
					'fixed left-1/2 top-1/2 z-50 grid w-full max-w-lg -translate-x-1/2 -translate-y-1/2 gap-4 border bg-background px-6 py-4 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-xl',
					props.class
				)
			"
		>
			<!-- Header -->
			<div class="flex items-center justify-between" v-if="!noHeader">
				<slot name="header" />
				<DialogClose
					class="outline-none focus:ring-2 ring-gray-300 rounded-md p-1 opacity-70 hover:opacity-100 transition-opacity"
				>
					<X class="w-4 h-4" stroke-width="1.5" />
					<span class="sr-only">Close</span>
				</DialogClose>
			</div>

			<slot />
		</DialogContent>
	</DialogPortal>
</template>
