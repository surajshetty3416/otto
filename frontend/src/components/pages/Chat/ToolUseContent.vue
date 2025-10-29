<template>
	<!-- Tool Use Details -->
	<div v-if="isOpen" class="bg-gray-50 rounded-md border border-gray-200 my-1.5">
		<!-- Tool Use Header -->
		<div
			class="flex items-center justify-between border-b border-gray-200 p-1.5 cursor-pointer"
			@click.stop="isOpen = false"
			title="Hide Tool Use"
		>
			<h3 class="text-gray-800 text-xs font-semibold flex items-center gap-1.5">
				<Wrench class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
				{{ title }}

				<span
					:title="content.status"
					class="w-1 h-1 bg-gray-300 rounded-full"
					:class="{
						'bg-yellow-400': content.status === 'pending',
						'bg-green-400': content.status === 'success',
						'bg-red-400': content.status === 'error',
					}"
				></span>
			</h3>

			<button @click="isOpen = false">
				<X class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
			</button>
		</div>

		<!-- Tool Use Details -->
		<div>
			<div class="border-b">
				<p class="text-xs font-medium text-gray-600 px-1.5 pt-1.5">Args</p>
				<template v-for="arg in Object.keys(content.args)" :key="arg">
					<div v-if="!(config?.use_explanation && arg === 'explanation')">
						<p class="text-xs italic font-medium text-gray-600 px-1.5 pt-1.5">
							{{ arg }}
						</p>
						<pre class="text-sm text-gray-800 px-1.5 pb-1.5">{{
							content.args[arg]
						}}</pre>
					</div>
				</template>
				<p
					v-if="config?.use_explanation && content.args.explanation"
					title="Explanation given by the LLM for using this tool"
					class="text-xs text-gray-600 border-t border-dashed border-gray-300 p-1.5"
				>
					{{ content.args.explanation }}
				</p>
			</div>

			<div class="p-1.5" title="Result of the tool use">
				<p class="text-sm font-medium text-gray-600">Result</p>
				<pre class="text-sm text-gray-800 pt-2">{{ content.result }}</pre>
			</div>
		</div>
	</div>

	<!-- Open Tool Use -->
	<div v-else class="inline-block mr-1.5 my-1.5">
		<button
			@click="isOpen = true"
			class="bg-gray-50 border border-gray-200 py-1.5 px-2 w-fit rounded-full flex items-center gap-1.5"
		>
			<Wrench class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
			<p class="text-sm font-medium text-gray-700">
				{{ title }}
			</p>
			<div
				v-if="content.status !== 'success'"
				class="w-1 h-1 bg-gray-300 rounded-full"
				:class="{
					'bg-yellow-400': content.status === 'pending',
					'bg-red-400': content.status === 'error',
				}"
			></div>
		</button>
	</div>
</template>
<script setup lang="ts">
import type { ToolUseContent } from "@/client/generated.types";
import { Wrench, X } from "lucide-vue-next";
import { computed, inject, ref } from "vue";
import { pendingRequestsKey, toolConfigKey } from "./utils";

const props = defineProps<{
	content: ToolUseContent;
}>();

const toolConfigs = inject(toolConfigKey);
const pendingRequests = inject(pendingRequestsKey);
const isOpen = ref(false);

const slug = computed(() => props.content.name);
const config = computed(() => toolConfigs?.value[slug.value]);
const title = computed(() => config.value?.title ?? slug.value);

const isAwaitingPermission = computed(() => {
	if (!pendingRequests) return false;
	return !!pendingRequests[props.content.id];
});

/**
 * show a semi-collapsed div (hide args) when permission request is required
 * pill is inline, i.e. multiple tool calls should be shown in a row
 * full width is when user clicks the i button
 *
 * When 'show detailed stats' is enabled show: duration, begin time, end time,
 * stdout, stderr, permission
 */
</script>
