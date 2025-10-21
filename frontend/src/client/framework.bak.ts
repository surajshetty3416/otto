/**
 * This file contains definitions for API calls to common functions in the
 * Frappe Framework using the v1 API:
 *
 * https://docs.frappe.io/framework/user/en/api/rest
 *
 * These are not dynamically defined like the v2 API handling in `./api.ts`
 */
import { callAPIv1 } from "./call";
import type { ReactiveCall } from "./types";

function login(username: string, password: string): ReactiveCall {
  const body = { usr: username, pwd: password };
  return callAPIv1("/api/method/login", { body });
}

function logout(): ReactiveCall {
  return callAPIv1("/api/method/logout");
}

export const framework = {
  login,
  logout,
};
