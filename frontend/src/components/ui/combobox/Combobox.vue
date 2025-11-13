<template>
	<Popover v-model:open="isOpen">
		<PopoverTrigger as-child>
			<Button :variant="variant" :size="size" :disabled="disabled">
				<div class="flex items-center gap-2">
					<span v-if="modelValue" :class="fontSizeClasses">
						{{ label }}
					</span>
					<span
						v-else="placeholder"
						class="text-ink-gray-4 text-sm"
						:class="fontSizeClasses"
					>
						{{ placeholder ?? "Select option" }}
					</span>
					<ChevronsUpDown class="size-3.5 text-ink-gray-4 p-0 shrink-0" />
				</div>
			</Button>
		</PopoverTrigger>
		<PopoverContent class="w-fit p-0 rounded-lg">
			<div class="flex flex-col">
				<!-- Input -->
				<div v-if="showSearch" class="border-b flex items-center gap-2 px-2 py-2">
					<Search class="size-3.5 text-ink-gray-4 p-0 shrink-0" />
					<input
						type="text"
						v-model="search"
						class="m-0 border-none focus:ring-0 focus:outline-none p-0 shrink w-full"
						:class="fontSizeClasses"
						ref="search-input"
					/>
					<LoadingIndicator
						v-if="loading"
						class="size-3.5 text-ink-gray-4 p-0 shrink-0"
					/>
				</div>

				<slot :options="options" :select="select" :cursor="cursor">
					<!-- Items -->
					<div class="max-h-48 overflow-y-auto p-1 min-w-32 flex flex-col gap-2">
						<template v-for="(option, index) in options" :key="option.value">
							<div
								:data-index="index"
								@click="select(option)"
								class="px-2 py-1.5 text-gray-800 hover:bg-gray-100 cursor-pointer rounded-md flex items-center justify-between"
								:class="[fontSizeClasses, { 'bg-gray-200': cursor === index }]"
								:onmouseover="() => (cursor = index)"
							>
								<div>
									<p class="font-medium">
										{{ option.label }}
									</p>
									<p
										v-if="option.label !== option.value"
										class="text-ink-gray-5 text-sm mt-1"
									>
										{{ option.value }}
									</p>
								</div>
								<Check
									v-if="option.value === modelValue"
									class="size-3.5 text-gray-700 p-0 shrink-0"
								/>
							</div>
						</template>
					</div>
				</slot>
				<div v-if="options.length === 0" class="px-2 py-2 text-sm text-ink-gray-4">
					No results found
				</div>
			</div>
		</PopoverContent>
	</Popover>
</template>

<script setup lang="ts">
import { Button } from "@/components/fui/Button";
import LoadingIndicator from "@/components/fui/LoadingIndicator.vue";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import shortcuts from "@/shortcuts";
import { Check, ChevronsUpDown, Search } from "lucide-vue-next";
import { computed, ref, watchEffect } from "vue";
import type { ComboboxOption, ComboboxProps } from "./types";

const isOpen = ref(false);
const cursor = ref(0);

const searchInput = ref<HTMLInputElement | null>(null);
const props = withDefaults(defineProps<ComboboxProps>(), {
	size: "sm",
	variant: "subtle",
	showSearch: true,
	loading: false,
});

const modelValue = defineModel<string | null>({ required: true });
const search = defineModel<string>("search", { required: false });
const label = computed(() => {
	return props.options.find((option) => option.value === modelValue.value)?.label;
});

function select(option: ComboboxOption) {
	modelValue.value = option.value;
	isOpen.value = false;
}

watchEffect(() => {
	if (!isOpen.value) {
		search.value = "";
		return;
	}
	searchInput.value?.focus();
});

watchEffect(() => {
	if (cursor.value < 0) cursor.value = 0;
	if (cursor.value >= props.options.length) cursor.value = props.options.length - 1;

	const index = document.querySelector(`[data-index="${cursor.value}"]`);
	if (index) {
		index.scrollIntoView({ behavior: "instant", block: "nearest" });
	}
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

function handleCursorUp() {
	cursor.value = Math.max(0, cursor.value - 1);
}

function handleCursorDown() {
	cursor.value = Math.min(props.options.length - 1, cursor.value + 1);
}

function handleSelectItem() {
	select(props.options[cursor.value]);
}

watchEffect(() => {
	if (isOpen.value) {
		shortcuts.on("cursor-up", handleCursorUp);
		shortcuts.on("cursor-down", handleCursorDown);
		shortcuts.on("select-item", handleSelectItem);
	} else {
		shortcuts.off("cursor-up", handleCursorUp);
		shortcuts.off("cursor-down", handleCursorDown);
		shortcuts.off("select-item", handleSelectItem);
	}
});
</script>
