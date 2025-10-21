/**
 * This file contains definitions for API calls to common functions in the
 * Frappe Framework using the v1 API:
 *
 * https://docs.frappe.io/framework/user/en/api/rest
 *
 * These are not dynamically defined like the v2 API handling in `./api.ts`
 */
import { callAPIv1 } from "./call";
import type { OttoDocTypes } from "./generated.types";
import type { GetList, Modifier, ReactiveCall } from "./types";

const KEY_MAP: Record<string, string | undefined> = {
  start: "limit_start",
  page_length: "limit_page_length",
  order_by: "order_by",
  group_by: "group_by",
};

function login(username: string, password: string): ReactiveCall {
  const body = { usr: username, pwd: password };
  return callAPIv1("/api/method/login", { body });
}

function logout(): ReactiveCall {
  return callAPIv1("/api/method/logout");
}

function get_list<
  Doc extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[Doc] & string
>(
  doctype: Doc,
  fields: Field[],
  options?: {
    start?: number;
    page_length?: number;
    filters?: Record<string, unknown>;
    or_filters?: Record<string, unknown>;
    order_by?: `${Field} ${"asc" | "desc"}`;
    group_by?: Field;
  },
  modifier?: Modifier
): GetList<Doc, Field> {
  const params: Record<string, unknown> = { fields };
  options ??= {};

  for (const [_key, value] of Object.entries(options)) {
    if (value === undefined) continue;

    const key = KEY_MAP[_key] ?? _key;
    params[key] = value;
  }

  return callAPIv1<Pick<OttoDocTypes[Doc], Field>[]>(
    `/api/resource/${doctype}`,
    { params },
    "GET",
    modifier
  );
}
function new_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  data: Partial<OttoDocTypes[Name]>,
  modifier?: Modifier
): ReactiveCall<OttoDocTypes[Name]> {
  return callAPIv1(
    `/api/resource/${doctype}`,
    { body: data },
    "POST",
    modifier
  );
}

function get_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  name: string,
  modifier?: Modifier
): ReactiveCall<OttoDocTypes[Name]> {
  return callAPIv1(`/api/resource/${doctype}/${name}`, {}, "GET", modifier);
}

function update_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  name: string | number,
  data: Partial<OttoDocTypes[Name]>,
  modifier?: Modifier
): ReactiveCall<OttoDocTypes[Name]> {
  return callAPIv1(
    `/api/resource/${doctype}/${name}`,
    { body: data },
    "PUT",
    modifier
  );
}

function delete_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  name: string | number,
  modifier?: Modifier
): ReactiveCall<"ok"> {
  return callAPIv1(`/api/resource/${doctype}/${name}`, {}, "DELETE", modifier);
}

export const framework = {
  login,
  logout,
  get_list,
  // CRUD calls
  new_doc,
  get_doc,
  update_doc,
  delete_doc,
};
