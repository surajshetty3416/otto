import { getMeta, useList } from "@/client";
import type { OttoDocTypes } from "@/client/generated.types";
import { reactive, ref, watchEffect } from "vue";
import type { LinkOption } from "./types";
import type { Call } from "@/client/call";
import type { GetListReturn } from "@/client/types";

export function useLinkOptions<
  Doc extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[Doc] & string
>(doctype: Doc, fieldname: Field, fields?: string[]) {
  const listholder = { list: null } as {
    list: ReturnType<typeof useList<any, any>> | null;
  };
  const loading = ref(true);
  const options = reactive<LinkOption[]>([]);
  const isEnd = ref(false);
  const call = ref<Call<undefined, GetListReturn<any, any>> | null>(null);

  async function next() {
    await listholder.list?.next();
  }

  (async function () {
    const params = await _getLinkOptionParams(doctype, fieldname, fields);
    const list = useList(params.doctype, params.fields, {
      filters: params.filters,
    });
    listholder.list = list;
    call.value = list.call.value;

    const lastIndex = ref(0);

    const unwatch = watchEffect(() => {
      loading.value = list.call.value?.loading ?? true;
      isEnd.value = list.isEnd.value;
      if (!list.call.value?.data) return;

      const _options = getOptionsFromListItem(
        list.call.value?.data,
        params.titleField
      );
      if (!list.call.value?.done) {
        options.push(..._options);
        return;
      }

      options.length = lastIndex.value;
      options.push(..._options);
      lastIndex.value = options.length;

      if (list.isEnd.value) {
        unwatch();
        call.value = null; // allow call to be garbage collected
      }
    });
  })();

  return {
    options,
    next,
    isEnd,
    call,
    loading,
  };
}

async function _getLinkOptionParams(
  doctype: keyof OttoDocTypes,
  fieldname: string,
  fields?: string[]
) {
  const meta = await getMeta(doctype);
  const fieldMeta = meta.fields.find((field) => field.fieldname === fieldname);
  if (!fieldMeta)
    throw new Error(`Field ${fieldname} not found in doctype ${doctype}`);

  if (fieldMeta.fieldtype !== "Link" || !fieldMeta.options)
    throw new Error(
      `Field ${fieldname} in doctype ${doctype} is not a Link field or does not have options`
    );

  const optionsDoctype = fieldMeta.options as keyof OttoDocTypes;
  const oMeta = await getMeta(optionsDoctype);

  const oFields: (keyof OttoDocTypes[typeof optionsDoctype])[] = ["name"];
  let titleField = "name";
  if (oMeta.title_field) {
    oFields.push(
      oMeta.title_field as keyof OttoDocTypes[typeof optionsDoctype]
    );
    titleField = oFields.at(-1) ?? "name";
  }

  if (fields) {
    oFields.push(...(fields as (keyof OttoDocTypes[typeof optionsDoctype])[]));
  }

  let filters = null;
  if (fieldMeta.link_filters) {
    filters = JSON.parse(fieldMeta.link_filters);
  }

  return {
    titleField,
    doctype: optionsDoctype,
    fields: oFields,
    filters,
  };
}

function getOptionsFromListItem(
  data: Record<string, unknown>[],
  titleField: string
): LinkOption[] {
  return data.map((item) => ({
    label: item[titleField || "name"] as string,
    value: item.name as string,
    item: item,
  }));
}
