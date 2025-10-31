<template>
	<!-- Collapsed Tool Use Pill -->
	<div class="inline-block mr-1.5">
		<button
			@click="isOpen = !isOpen"
			class="bg-gray-50 border border-gray-200 py-1.5 px-2 w-fit rounded-full flex items-center gap-1.5"
			:class="isOpen ? 'ring-2 ring-gray-400' : ''"
		>
			<Wrench class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
			<p class="text-sm font-medium text-gray-700">
				{{ title }}
			</p>
			<IndicatorDot v-if="content.status !== 'success' && !request" :color="statusColor" />
			<div
				v-if="request"
				class="ml-2 flex items-center gap-1"
				title="Permission required to run this tool"
			>
				<SmallButton
					:rounded="true"
					:loading="acknowledge_request.loading"
					@click.stop="
						acknowledge_request.run({ request_id: request.name, status: 'Denied' })
					"
				>
					<X class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
				</SmallButton>
				<SmallButton
					:isPrimary="true"
					:rounded="true"
					:loading="acknowledge_request.loading"
					@click.stop="
						acknowledge_request.run({ request_id: request.name, status: 'Granted' })
					"
				>
					<Check class="h-3.5 w-3.5 text-gray-700 flex-shrink-0" stroke-width="1.5" />
				</SmallButton>
			</div>
		</button>
	</div>

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

				<IndicatorDot :color="statusColor" />
			</h3>

			<button @click="isOpen = false">
				<X class="h-3.5 w-3.5 text-gray-800 flex-shrink-0" stroke-width="1.5" />
			</button>
		</div>

		<!-- Tool Use Details -->
		<div>
			<!-- Args container -->
			<div v-if="Object.keys(content.args).length > 0">
				<template v-for="arg in args" :key="arg.name">
					<div>
						<p
							class="text-xs italic font-medium text-gray-600 px-1.5 pt-1.5 capitalize"
							:title="`Argument name: ${arg.name}`"
						>
							{{ arg.name }}
						</p>
						<pre
							class="text-sm text-gray-800 px-1.5 pb-1.5 pt-0.5"
							:title="`Argument value: ${arg.value}`"
							>{{ arg.value }}</pre
						>
					</div>
				</template>
			</div>

			<!-- Explanation  -->
			<p
				v-if="config?.use_explanation && content.args.explanation"
				title="Explanation given by the LLM for using this tool"
				class="text-xs text-gray-600 border-t border-gray-200 p-1.5"
			>
				{{ content.args.explanation }}
			</p>

			<!-- Result container -->
			<div
				v-if="content.status !== 'pending'"
				class="p-1.5 border-t"
				title="Result of the tool use"
			>
				<p class="text-xs italic font-medium text-gray-600">Result</p>
				<pre class="text-sm text-gray-800 pt-0.5">{{ content.result }}</pre>
			</div>

			<!-- Permission container -->
			<div v-if="request" class="p-1.5 flex items-center justify-between border-t">
				<div class="flex items-center gap-2">
					<IndicatorDot color="yellow" />
					<p class="text-sm font-medium text-gray-700">Allow running this tool?</p>
				</div>

				<div class="ml-2 flex items-center gap-1">
					<SmallButton
						:loading="acknowledge_request.loading"
						@click="
							acknowledge_request.run({
								request_id: request.name,
								status: 'Denied',
							})
						"
						>No</SmallButton
					>
					<SmallButton
						:loading="acknowledge_request.loading"
						:isPrimary="true"
						@click="
							acknowledge_request.run({
								request_id: request.name,
								status: 'Granted',
							})
						"
						>Yes</SmallButton
					>
				</div>
			</div>
		</div>
	</div>
</template>
<script setup lang="ts">
import type { ToolUseContent } from "@/client/generated.types";
import { Check, Wrench, X } from "lucide-vue-next";
import { computed, inject, ref } from "vue";
import { pendingRequestsKey, toolConfigKey } from "./utils";
import IndicatorDot from "@/components/ui/IndicatorDot.vue";
import SmallButton from "./SmallButton.vue";
import { api } from "@/client";

/**
 * show a semi-collapsed div (hide args) when permission request is required
 * pill is inline, i.e. multiple tool calls should be shown in a row
 * full width is when user clicks the i button
 *
 * When 'show detailed stats' is enabled show: duration, begin time, end time,
 * stdout, stderr, permission
 */

const props = defineProps<{
	content: ToolUseContent;
}>();

const toolConfigs = inject(toolConfigKey);
const pendingRequests = inject(pendingRequestsKey);
const isOpen = ref(false);

const slug = computed(() => props.content.name);
const config = computed(() => toolConfigs?.value[slug.value]);
const title = computed(() => config.value?.title ?? slug.value);
const args = computed(() => {
	const args: { name: string; value: unknown }[] = [];
	for (const [name, value] of Object.entries(props.content.args)) {
		if (config.value?.use_explanation && name === "explanation") continue;
		args.push({ name, value });
	}
	return args;
});

const request = computed(() => pendingRequests?.[props.content.id]);

const acknowledge_request = api.chat.acknowledge_request(
	{ request_id: "", status: "Granted" },
	{ auto: false }
);

const statusColor = computed(() => {
	if (props.content.status === "pending") return "yellow";
	if (props.content.status === "error") return "red";
	if (props.content.status === "success") return "green";
	return "gray";
});
</script>
