import type { ModelDetails } from "@/client/generated.types";

export function modelName(model: ModelDetails): string {
  return model.title.slice(model.provider.length + 1);
}
