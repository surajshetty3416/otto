<template>
	<div class="flex h-screen w-screen justify-center bg-surface-gray-2">
		<div class="mt-32 w-full px-4">
			<Logo class="mx-auto h-8 w-8" />
			<h1
				class="mt-6 flex items-center justify-center space-x-1.5 text-3xl font-semibold text-ink-gray-9"
			>
				Login to Otto
			</h1>
			<form
				class="mx-auto mt-6 w-full px-4 sm:w-96 space-y-4"
				method="POST"
				action="/api/method/login"
				@submit.prevent="submit"
			>
				<TextInput
					variant="outline"
					size="md"
					:type="(email || '').toLowerCase() === 'administrator' ? 'text' : 'email'"
					label="Email"
					v-model="email"
					placeholder="jane@example.com"
					:disabled="session.login?.loading"
				/>
				<TextInput
					class="mt-4"
					variant="outline"
					size="md"
					label="Password"
					v-model="password"
					placeholder="••••••"
					:disabled="session.login?.loading"
					type="password"
				/>
				<ErrorMessage
					v-if="session.login?.failed"
					class="mt-2"
					message="Failed to login"
				/>
				<Button variant="solid" class="mt-6 w-full" :loading="session.login?.loading">
					Login
				</Button>
			</form>
		</div>
	</div>
</template>
<script setup lang="ts">
import { reactive, ref, type Reactive } from "vue";

import type { Call } from "../../client/types";
import router, { defaultRouteName } from "../../router";
import Button from "../fui/Button/Button.vue";
import ErrorMessage from "../fui/ErrorMessage.vue";
import TextInput from "../fui/TextInput.vue";
import Logo from "../svg/Logo.vue";
import { api } from "../../client";

const email = ref("");
const password = ref("");
const session = reactive({}) as Reactive<{ login?: Call }>;

function submit() {
	session.login = api.login(email.value, password.value);
	session.login.then(() => router.push({ name: defaultRouteName }));
}
</script>
