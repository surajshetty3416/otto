<template>
	<router-view />
	<Toaster position="bottom-right" :close-button="true" close-button-position="top-right" />
</template>

<script setup lang="ts">
import { Toaster } from "vue-sonner";
import "vue-sonner/style.css";
</script>
