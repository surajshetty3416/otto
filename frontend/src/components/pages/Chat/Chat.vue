<template>
	<div class="w-screen h-screen flex items-center justify-center bg-gray-50">
		<div class="flex">
			<input
				type="text"
				v-model="message"
				placeholder="Message"
				class="px-4 py-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
			/>
			<button
				@click="test"
				class="px-4 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600 transition"
			>
				Echo
			</button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { api } from "../../../client";

const message = ref("test message");

async function test() {
	const call = api.echo({ message: message.value }, { cache: true });
	call.then((data) => {
		console.log(`first: '${data}'`);
	});

	const re = await api.echo({ message: message.value });
	console.log(`second: '${re}'`);

	const llms = await api.get_list("Otto LLM", ["name", "size", "provider"], undefined, {
		cache: true,
	});
	console.log("llms", llms);
}
</script>
