<template>
	<main class="flex">
		<Sidebar />
		<!-- <div class="p-2 w-10 h-screen bg-gray-50 border-r border-gray-200">
			<p class="text-xs text-purple-600 border-b border-gray-200 pb-2">Otto</p>
		</div> -->
		<router-view class="w-full"></router-view>
	</main>
</template>

<script setup lang="ts">
import shortcuts from "@/shortcuts";
import { onMounted, onUnmounted } from "vue";
import Sidebar from "../ui/sidebar/Sidebar.vue";
import router from "@/router";

onMounted(() => {
	shortcuts.on("new-chat", newChat);
});

onUnmounted(() => {
	shortcuts.off("new-chat", newChat);
});

function newChat(e: KeyboardEvent) {
	const currentRoute = router.currentRoute.value;
	if (currentRoute.name === "Chat" && !currentRoute.params.chatId) return;

	e.preventDefault();
	e.stopPropagation();
	router.push({ name: "Chat" });
}
</script>
