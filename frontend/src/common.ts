import { computed } from "vue";
import { list_assistants, list_models } from "./client";
import type { Assistant, ModelDetails } from "./client/generated.types";

export const assistants = computed(() => {
  if (!list_assistants.data) return {};
  return list_assistants.data.reduce((acc, assistant) => {
    acc[assistant.name] = assistant;
    return acc;
  }, {} as Record<string, Assistant>);
});

export const models = computed(() => {
  if (!list_models.data) return {};

  return list_models.data.reduce((acc, model) => {
    acc[model.name] = model;
    return acc;
  }, {} as Record<string, ModelDetails>);
});
