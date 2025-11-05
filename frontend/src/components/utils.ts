import type { ModelDetails } from "@/client/generated.types";
import { models } from "@/common";

export function modelName(model: ModelDetails | string): string {
  if (typeof model === "string") {
    model = models.value[model];
  }

  return model.title.slice(model.provider.length + 1);
}
