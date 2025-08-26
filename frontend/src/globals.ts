import { reactive, type Reactive } from "vue";
import type { Globals } from "./types";

const g: Reactive<Globals> = reactive({});

export function useGlobals() {
  // For use in script setup
  return g;
}
