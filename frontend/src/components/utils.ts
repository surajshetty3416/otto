import { getFieldMeta } from "@/client";
import type { ModelDetails, OttoDocTypes } from "@/client/generated.types";
import type { FieldMeta } from "@/client/meta.types";
import { models } from "@/common";
import { ref } from "vue";

export function modelName(model: ModelDetails | string): string {
  if (typeof model === "string") {
    model = models.value[model];
  }

  return model.title.slice(model.provider.length + 1);
}

export function useMeta(doctype?: keyof OttoDocTypes, fieldname?: string) {
  const meta = ref<FieldMeta | undefined>(undefined);
  if (!doctype || !fieldname) return meta;

  getFieldMeta(doctype, fieldname).then((m) => {
    meta.value = m;
  });

  return meta;
}
