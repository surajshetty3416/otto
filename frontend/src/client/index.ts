/* Check `./README.md` for information. */

import type { GetListOptions, GetListReturn } from "@/client/types";
import { reactive, ref, watchEffect } from "vue";
import { api, framework } from "./api";
import type { Call } from "./call";
import type { OttoDocTypes } from "./generated.types";
import type { DocTypeMeta, FieldMeta } from "./meta.types";

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
const configForOnce = {
  cache: true,
  once: true,
  ttl: 60 * 60 * 24,
}; // 1 day
framework.get_meta("Otto LLM", configForOnce);
framework.get_meta("Otto Chat", configForOnce);
framework.get_meta("Otto Assistant", configForOnce);

const _metaCache = new Map<string, DocTypeMeta>();
const _fieldMetaCache = new Map<string, FieldMeta>();

/**
 * Helper functions and composibles over raw framework calls.
 */

export async function getMeta(
  doctype: keyof OttoDocTypes
): Promise<DocTypeMeta> {
  if (_metaCache.has(doctype)) {
    return _metaCache.get(doctype)!;
  }

  const config = { ...configForOnce, auto: undefined };
  const meta = await framework.get_meta(doctype, config);
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

/**
 * A convenient wrapper around the framework.get_list call.
 *
 * Use options to specify the initial start (default 0) and limit (default 20), and to filter the items.
 *
 * Returned values:
 * - `next` is a function that fetches the next page of items, it returns a Promise that resolves to the items fetched (not reactive).
 * - `call` is the last call made to `get_list` this can be checked  for errors, loading, etc.
 * - `items` is the reactive list of items fetched so far
 * - `isEnd` is a boolean indicating if the end of the list has been reached
 */
export function useList<
  Doc extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[Doc] & string
>(doctype: Doc, fields: Field[], options?: GetListOptions<Field>) {
  const offset = options?.start ?? 0;
  const items = reactive<GetListReturn<Doc, Field>>([]);
  const page = ref((options?.start ?? 0) - 1);
  const limit = ref(options?.limit ?? 20);
  const isEnd = ref(false);
  const lastIndex = ref(0);
  const call = ref<Call<undefined, GetListReturn<Doc, Field>> | null>(null);

  async function next(): Promise<GetListReturn<Doc, Field> | undefined> {
    if (isEnd.value) return;

    page.value += 1;

    const _options = {
      ...options,
      start: page.value * limit.value + offset,
      limit: limit.value,
    };

    const _call = framework.get_list(doctype, fields, _options, {
      cache: true,
    });
    call.value = _call;

    return new Promise((resolve) => {
      const unwatch = watchEffect(() => {
        if (!_call.data) return;

        if (!_call.done) {
          // @ts-expect-error - items is reactive, _items is not
          items.push(..._call.data);
          return;
        }

        items.length = lastIndex.value;

        // @ts-expect-error - items is reactive, _items is not
        items.push(..._call.data);
        lastIndex.value = items.length;
        isEnd.value = _call.data.length < limit.value;
        unwatch();
        if (isEnd.value) call.value = null; // allow call to be garbage collected
        return resolve(_call.data);
      });
    });
  }

  next();
  return { items, next, call, isEnd };
}
