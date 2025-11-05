<template>
	<TextLoadingIndicator v-if="get_user_info.loading" text="Loading user" />
	<div v-else-if="get_user_info.data" class="flex items-center overflow-hidden justify-between">
		<!-- Avatar -->
		<!-- <div class="w-4.5 h-4.5 bg-gray-200 rounded-full shrink-0 overflow-hidden">
			<p v-else class="text-lg text-gray-400 text-center" style="font-weight: 900">
				{{ get_user_info.data.name[0] }}
			</p>
		</div> -->

		<!-- Name -->
		<p
			v-if="!isCollapsed"
			:class="{ 'opacity-0': isCollapsed }"
			class="text-sm font-medium text-gray-600 text-nowrap"
		>
			{{ get_user_info.data.name }}
		</p>

		<TextTooltip
			:delay="0"
			@click="logout()"
			content="Logout"
			side="right"
			align="center"
			:sideOffset="8"
			class="text-gray-600 hover:text-gray-800"
		>
			<LogOutIcon class="w-3.5 h-3.5" stroke-width="1.5" />
		</TextTooltip>
	</div>
</template>
<script setup lang="ts">
import { framework, get_user_info } from "@/client";
import { toLogin } from "@/client/utils";
import { LogOutIcon } from "lucide-vue-next";
import TextLoadingIndicator from "../TextLoadingIndicator.vue";
import TextTooltip from "../tooltip/TextTooltip.vue";

defineProps<{
	isCollapsed: boolean;
}>();

async function logout() {
	await framework.logout();
	toLogin(false);
}
</script>
