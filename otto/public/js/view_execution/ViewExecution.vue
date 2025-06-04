<script setup>
import { ref } from "vue";

const execution = ref("test this");
</script>

<template>
	<div>
		<h1>{{ execution }}</h1>
	</div>
</template>

<style lang="scss" scoped></style>
