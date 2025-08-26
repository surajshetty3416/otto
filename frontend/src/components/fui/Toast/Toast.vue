<template>
	<div class="my-2 min-w-[15rem] max-w-[40rem] rounded-lg border bg-surface-white p-4 shadow-md">
		<div class="flex items-start">
			<div v-if="icon" class="mr-3 grid h-5 w-5 place-items-center">
				<Icon :name="icon" :class="['h-5 w-5', iconClasses]" />
			</div>
			<div>
				<slot>
					<p
						v-if="title"
						class="text-base font-medium text-ink-gray-9"
						:class="{ 'mb-1': message }"
						v-html="title"
					></p>
					<p v-if="message" class="text-base text-ink-gray-5" v-html="message"></p>
				</slot>
			</div>
			<div class="ml-auto pl-2">
				<slot name="actions">
					<button
						class="grid h-5 w-5 place-items-center rounded"
						@click="$emit('close')"
					>
						<X class="h-4 w-4 text-ink-gray-7" />
					</button>
				</slot>
			</div>
		</div>
	</div>
</template>
<script lang="ts" setup>
import { X } from "lucide-vue-next";
import { onMounted } from "vue";
import type { ToastProps } from "./types";
import Icon from "../Icon.vue";

const props = defineProps<ToastProps>();

const emit = defineEmits<{
	(e: "close"): void;
}>();

onMounted(() => {
	const duration = props.duration ?? 5000;
	if (duration <= 0) return;
	setTimeout(() => emit("close"), duration);
});
</script>
