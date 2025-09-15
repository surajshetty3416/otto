<template>
	<div class="flex justify-center">
		<!-- container -->
		<div
			class="border border-gray-300 h-full flex flex-col justify-between"
			style="width: 728px"
		>
			<!-- Messages -->
			<div class="p-4 w-full flex flex-col gap-4">
				<div
					v-for="message in messages"
					:key="message.id"
					class="w-full flex text-gray-900"
				>
					<!-- User -->
					<p
						v-if="message.role === 'user'"
						class="bg-gray-100 px-3 py-1 rounded-md w-fit ml-auto"
					>
						{{ message.content }}
					</p>

					<!-- Assistant -->
					<p v-else class="w-full">{{ message.content }}</p>
				</div>
			</div>

			<!-- Input -->
			<div class="flex items-center space-between p-4 border-t gap-2 bottom-0 relative">
				<input
					v-model="query"
					type="text"
					class="border border-gray-300 rounded-full w-full py-1"
					@keypress.enter="send"
				/>
				<button
					@click="send"
					class="monospace bg-gray-300 rounded-full w-8 h-8 flex items-center justify-center"
				>
					⌃
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from "vue";
import socket from "../../../socket";
import { api } from "../../../client";

interface Message {
	id: string;
	role: "user" | "assistant";
	content: string;
}

interface Chunk {
	type: "text" | "thinking" | "tool_use" | "system";
	content: string;
	item_id: string;
	session_id: string;
}

const query = ref("");

const messages = reactive<Message[]>([
	{ id: "0", role: "user", content: "Hello!" },
	{ id: "1", role: "assistant", content: "Hello, I am Otto, how can I help you today?" },
	{ id: "2", role: "user", content: "what's the capital of France?" },
	{ id: "3", role: "assistant", content: "Paris" },
	{ id: "4", role: "user", content: "what's the capital of Germany?" },
	{ id: "5", role: "assistant", content: "Berlin" },
]);

const cache: Record<string, Message> = {};
function get(id: string): Message | undefined {
	if (cache[id]) {
		return cache[id];
	}

	const message = messages.find((message) => message.id === id);
	if (message) cache[id] = message;
	return message;
}

function random() {
	return Math.random().toString(36).substring(2, 15);
}

async function send() {
	if (!query.value) return;

	messages.push({ id: random(), role: "user", content: query.value });
	query.value = "";

	const res = await api.chat.chat({ query: query.value });
	console.log("res", res);
}

function responseHandler(data: Chunk) {
	let item: Message | undefined = get(data.item_id);
	if (!item) {
		messages.push({ id: data.item_id, role: "assistant", content: "" });
	}

	item = get(data.item_id);
	if (!item) {
		return;
	}

	switch (data.type) {
		case "text":
			item.content += data.content;
			break;
		case "thinking":
			item.content += data.content;
			break;
	}
}

onMounted(() => {
	console.log("listeners set");
	socket.on("otto.api.chat", responseHandler);
});

onUnmounted(() => {
	console.log("listeners removed");
	socket.off("otto.api.chat", responseHandler);
});
</script>
