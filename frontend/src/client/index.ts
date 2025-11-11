/* Check `./README.md` for information. */

import { api, framework } from "./api";
import type { OttoDocTypes } from "./generated.types";
import type { FieldMeta, DocTypeMeta } from "./meta.types";

export { api, framework } from "./api";
export { call } from "./call";

/**
 * Common API calls used around the UI
 */
export const get_user = api.get_user();
export const get_user_info = api.get_user_info();
export const list_chats = api.chat.list_chats(null, { cache: true });
export const list_assistants = api.chat.list_assistants(null, { cache: true });
export const list_models = api.chat.list_models(null, { cache: true });

/**
 * Prefetch a few metas so that they are available and cached when needed.
 */
framework.get_meta("Otto Chat", { cache: true });
framework.get_meta("Otto Assistant", { cache: true });

const _metaCache = new Map<string, DocTypeMeta>();
const _fieldMetaCache = new Map<string, FieldMeta>();

export async function getMeta(
  doctype: keyof OttoDocTypes
): Promise<DocTypeMeta> {
  if (_metaCache.has(doctype)) {
    return _metaCache.get(doctype)!;
  }

  const meta = await framework.get_meta(doctype, { cache: true });
  _metaCache.set(doctype, meta);
  return meta;
}

export async function getFieldMeta(
  doctype: keyof OttoDocTypes,
  fieldname: string
): Promise<FieldMeta> {
  const key = `${doctype}::${fieldname}`;
  if (_fieldMetaCache.has(key)) {
    return _fieldMetaCache.get(key)!;
  }

  const meta = await getMeta(doctype);
  const fieldMeta = meta.fields.find((field) => field.fieldname === fieldname);
  if (!fieldMeta) {
    throw new Error(`Field ${fieldname} not found in doctype ${doctype}`);
  }

  _fieldMetaCache.set(key, fieldMeta);
  return fieldMeta;
}
