/**
 * This file contains definitions for API calls to common functions in the
 * Frappe Framework using the v1 and v2 APIs:
 *
 * https://docs.frappe.io/framework/user/en/api/rest
 * https://github.com/frappe/frappe/blob/develop/frappe/api/v2.py
 */
import { Call, callV1, callV2 } from "./call";
import type { OttoDocTypes } from "./generated.types";
import type { Config, GetListReturn } from "./types";

function login(username: string, password: string): Call<undefined, undefined> {
  const body = { usr: username, pwd: password };
  return callV1({ method: "POST", path: "method/login", body });
}

function logout(): Call<undefined, undefined> {
  return callV2({ method: "POST", path: "method/logout" });
}

function get_list<
  Doc extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[Doc] & string
>(
  doctype: Doc,
  fields: Field[] | ["*"],
  options?: {
    start?: number;
    limit?: number;
    filters?: Record<string, unknown>;
    or_filters?: Record<string, unknown>;
    order_by?: `${Field} ${"asc" | "desc"}`;
  },
  config?: Config
): Call<undefined, GetListReturn<Doc, Field>> {
  const params: Record<string, unknown> = { fields };
  for (const [key, value] of Object.entries(options ?? {})) {
    if (value === undefined) continue;

    params[key] = value;
  }

  return callV2({
    method: "GET",
    path: `document/${doctype}`,
    params,
    config,
  });
}

function new_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  data: Partial<OttoDocTypes[Name]>,
  config?: Config
): Call<undefined, OttoDocTypes[Name]> {
  return callV2({
    method: "POST",
    path: `document/${doctype}`,
    body: data,
    config,
  });
}

function get_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  name: string | number,
  config?: Config
): Call<undefined, OttoDocTypes[Name]> {
  return callV2({
    method: "GET",
    path: `document/${doctype}/${name}`,
    config,
  });
}

function update_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  name: string | number,
  data: Partial<OttoDocTypes[Name]>,
  config?: Config
): Call<undefined, OttoDocTypes[Name]> {
  return callV2({
    method: "PUT",
    path: `document/${doctype}/${name}`,
    body: data,
    config,
  });
}

function delete_doc<Name extends keyof OttoDocTypes>(
  doctype: Name,
  name: string | number,
  config?: Config
): Call<undefined, "ok"> {
  return callV2({
    method: "DELETE",
    path: `document/${doctype}/${name}`,
    config,
  });
}

export const handlers = {
  login,
  logout,
  get_list,
  // CRUD calls
  new_doc,
  get_doc,
  update_doc,
  delete_doc,
};
