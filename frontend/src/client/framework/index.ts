/**
 * This file contains definitions for API calls to common functions in the
 * Frappe Framework using the v1 and v2 APIs:
 *
 * https://docs.frappe.io/framework/user/en/api/rest
 * https://github.com/frappe/frappe/blob/develop/frappe/api/v2.py
 */
import { Call, callV1, callV2 } from "../call";
import type { OttoDocTypes } from "../generated.types";
import type { Config } from "../types";
import type { GetListReturn, GetListArgs } from "./types";

const KEY_MAP: Record<string, string | undefined> = {
  start: "limit_start",
  page_length: "limit_page_length",
  order_by: "order_by",
  group_by: "group_by",
};

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
  args: GetListArgs<Doc, Field>,
  config?: Config
): Call<undefined, GetListReturn<Doc, Field>> {
  const params: Record<string, unknown> = {};
  for (const [_key, value] of Object.entries(args)) {
    if (_key === "doctype") continue;
    if (value === undefined) continue;

    const key = KEY_MAP[_key] ?? _key;
    params[key] = value;
  }

  return callV2({
    method: "GET",
    path: `document/${args.doctype}`,
    params,
    config,
  });
}

function new_doc<Name extends keyof OttoDocTypes>(
  args: {
    doctype: Name;
    data: Partial<OttoDocTypes[Name]>;
  },
  config?: Config
): Call<undefined, OttoDocTypes[Name]> {
  return callV2({
    method: "POST",
    path: `resource/${args.doctype}`,
    body: args.data,
    config,
  });
}

function get_doc<Name extends keyof OttoDocTypes>(
  args: {
    doctype: Name;
    name: string;
  },
  config?: Config
): Call<undefined, OttoDocTypes[Name]> {
  return callV2({
    method: "GET",
    path: `document/${args.doctype}/${args.name}`,
    config,
  });
}

function update_doc<Name extends keyof OttoDocTypes>(
  args: {
    doctype: Name;
    name: string | number;
    data: Partial<OttoDocTypes[Name]>;
  },
  config?: Config
): Call<undefined, OttoDocTypes[Name]> {
  return callV2({
    method: "PUT",
    path: `document/${args.doctype}/${args.name}`,
    body: args.data,
    config,
  });
}

function delete_doc<Name extends keyof OttoDocTypes>(
  args: {
    doctype: Name;
    name: string | number;
  },
  config?: Config
): Call<undefined, "ok"> {
  return callV2({
    method: "DELETE",
    path: `document/${args.doctype}/${args.name}`,
    config,
  });
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
