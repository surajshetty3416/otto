<template>
	<!-- Toggle Tool Use Details -->
	<CollapsedContentToggle v-model="isOpen" v-bind="attrs">
		<Wrench class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
		<p class="text-sm font-medium text-gray-700">
			{{ title }}
		</p>
		<IndicatorDot v-if="content.status !== 'success' && !hasPending" :color="statusColor" />
		<div
			v-if="hasPending"
			class="ml-2 flex items-center gap-1"
			title="Permission required to run this tool"
		>
			<SmallButton :rounded="true" :loading="acknowledge_request.loading" @click.stop="deny">
				<X class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
			</SmallButton>
			<SmallButton
				:isPrimary="true"
				:rounded="true"
				:loading="acknowledge_request.loading"
				@click.stop="grant"
			>
				<Check class="h-3.5 w-3.5 text-gray-700 flex-shrink-0" stroke-width="1.5" />
			</SmallButton>
		</div>
	</CollapsedContentToggle>

	<!-- Tool Use Details -->
	<ContentContainer v-if="isOpen" v-bind="attrs">
		<!-- Tool Use Header -->
		<div
			class="flex items-center justify-between border-b border-gray-300 p-1.5 cursor-pointer"
			@click.stop="isOpen = false"
			:title="`Tool used: ${title}, Status: ${titlecase(content.status)}`"
		>
			<h3 class="text-gray-800 text-xs font-semibold flex items-center gap-2">
				<Wrench class="h-3.5 w-3.5 text-gray-600 flex-shrink-0" stroke-width="1.5" />
				<span title="Tool label">
					{{ title }}
				</span>
				<span
					title="Tool slug"
					v-if="config"
					class="font-mono text-xs font-medium text-gray-500"
				>
					{{ config.slug }}
				</span>

				<IndicatorDot
					class="self-center"
					:title="`Tool status: ${content.status}`"
					:color="statusColor"
				/>
			</h3>

			<button @click="isOpen = false" title="Hide Tool Use">
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
							class="text-sm text-gray-800 px-1.5 pb-1.5 pt-0.5 whitespace-pre-wrap"
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
				class="text-xs text-gray-600 border-t border-gray-300 p-1.5"
			>
				{{ content.args.explanation }}
			</p>

			<!-- Result container -->
			<div
				v-if="content.status !== 'pending'"
				class="p-1.5 border-t border-gray-300"
				title="Result of the tool use"
			>
				<p class="text-xs italic font-medium text-gray-600">Result</p>
				<pre class="text-sm text-gray-800 pt-0.5 overflow-x-auto">{{
					content.result
				}}</pre>
			</div>

			<!-- Permission container -->
			<div
				v-if="hasPending"
				class="p-1.5 flex items-center justify-between border-t border-gray-300"
			>
				<div class="flex items-center gap-2">
					<IndicatorDot color="yellow" />
					<p class="text-sm font-medium text-gray-700">Run this tool?</p>
				</div>

				<div class="ml-2 flex items-center gap-1">
					<SmallButton :loading="acknowledge_request.loading" @click="deny"
						>No</SmallButton
					>
					<SmallButton
						:loading="acknowledge_request.loading"
						:isPrimary="true"
						@click="grant"
						>Yes</SmallButton
					>
				</div>
			</div>
		</div>
	</ContentContainer>
</template>
<script setup lang="ts">
import { api } from "@/client";
import type { SessionItem, ToolUseContent } from "@/client/generated.types";
import { titlecase } from "@/components/format";
import IndicatorDot from "@/components/ui/IndicatorDot.vue";
import { Check, Wrench, X } from "lucide-vue-next";
import { computed, inject, ref, useAttrs, watch } from "vue";
import CollapsedContentToggle from "./CollapsedContentToggle.vue";
import ContentContainer from "./ContentContainer.vue";
import SmallButton from "./SmallButton.vue";
import { pendingRequestsKey, toolConfigKey } from "./utils";
const attrs = useAttrs();

/**
 * show a semi-collapsed div (hide args) when permission request is required
 * pill is inline, i.e. multiple tool calls should be shown in a row
 * full width is when user clicks the i button
 *
 * When 'show detailed stats' is enabled show: duration, begin time, end time,
 * stdout, stderr, permission
 *
 * Click arg to copy args object or individual arg value
 * Click result to copy result
 */

const props = defineProps<{
	item: SessionItem;
	content: ToolUseContent;
}>();

const toolConfigs = inject(toolConfigKey);
const pendingRequests = inject(pendingRequestsKey);

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
const isOpen = ref(!!request.value);

const acknowledge_request = api.chat.acknowledge_request(
	{ request_id: "", status: "Granted" },
	{ auto: false }
);
const hasPending = computed(() => !!request.value && !acknowledge_request.done);
function grant() {
	if (!request.value) return;
	acknowledge_request.run({ request_id: request.value.name, status: "Granted" }, false);
}
function deny() {
	if (!request.value) return;
	acknowledge_request.run({ request_id: request.value.name, status: "Denied" }, false);
}

const statusColor = computed(() => {
	if (hasPending.value) return "orange";
	if (props.content.status === "pending") return "yellow";
	if (props.content.status === "error") return "red";
	if (props.content.status === "success") return "green";
	return "gray";
});

watch(
	() => request.value,
	(newval) => {
		isOpen.value = !!newval;
	}
);
</script>
