import { reactive, type Reactive } from "vue";
import type { Call, ServerError } from "./types";
import { ui } from "../utils";

/**
 * Raw call to legacy FF API, used as a fallback when v2 doesn't work as expected.
 * Used only for calls to Framework defined endpoints.
 */
export function callAPIv1<T = unknown>(
  url: `/api/${string}`,
  args?: {
    body?: Record<string, unknown>;
    params?: Record<string, unknown>;
  },
  method: "GET" | "PUT" | "POST" | "DELETE" = "POST"
): Reactive<Call<T>> {
  args ??= {};

  const headers = getHeaders();
  const bodyJSON = args.body ? JSON.stringify(args.body) : undefined;
  const req: RequestInit = {
    method,
    headers,
    body: bodyJSON,
  };

  return getCall(`${encodeURI(url)}${getParams(args.params)}`, req, bodyJSON);
}

/**
 * Raw call to FF API v2: https://github.com/frappe/frappe/pull/22300. This is
 * not meant to be used by itself but through the `api.path.method()` way.
 *
 * Returns a Reactive<Call> object.
 */
export function callAPIv2(
  method: string,
  kwargs?: Record<string, unknown>
): Reactive<Call> {
  const headers = getHeaders();
  const bodyJSON = kwargs ? JSON.stringify(kwargs) : undefined;
  const req: RequestInit = {
    method: "POST",
    headers,
    body: bodyJSON,
  };

  return getCall(`/api/v2/method/otto.api.${method}`, req, bodyJSON);
}

function getCall<T = unknown>(
  url: string,
  req: RequestInit,
  body: string | undefined,
  reCall?: Reactive<Call<T>>
): Reactive<Call<T>> {
  const start = performance.now();

  const promise = fetch(url, req);
  const promiseJSON = promise
    .then((response) => {
      call.loading = false;
      call.failed = !response.ok;
      call.response = response;
      return response.json();
    })
    .then((json) => {
      if (!call.failed) {
        call.data = json.data ?? json.message;
      } else {
        call.errors = json.errors;
        logErrors(json.errors, call.url);
      }

      return json;
    });

  /**
   * If `call.then` as accessed then the below then handler is used. To
   * access the value of `call.data` following can be done:
   * - `const value = await call.then(...)`
   * - `call.then(value => { ... })`
   */
  const then_ = (resolve: (value: T) => any, reject?: (reason: any) => any) =>
    promiseJSON
      .then(() => {
        if (call.failed) throw getError(call); // Handled in chained catch

        if (window.DEBUG_API) {
          console.groupCollapsed(
            `%cAPI Response [${url}] ${getIndicator(call.data)}`,
            "color: lightgreen"
          );
          console.log("Duration", performance.now() - start, "ms");
          console.log("Data", call.data);
          console.groupEnd();
        }

        resolve(call.data as T);
      })
      .catch((error: any) => {
        if (!(error instanceof Error)) {
          logNonError(error);
          error = getError(call);
        }

        call.error = error;
        reject?.(error);
      });
  /**
   * If `call.catch` as accessed then the below catch handler is used. To
   * access the value of `call.data` following can be done:
   * - `const value = await call.catch(...)`
   * - `call.catch(...).then(value => { ... })`
   */
  const catch_ = (reject: (reason: any) => any) =>
    promiseJSON
      .then(async () => {
        if (call.failed) throw getError(call); // Handled in chained catch

        return call.data;
      })
      .catch((error: any) => {
        if (!(error instanceof Error)) {
          logNonError(error);
          error = getError(call);
        }

        call.error = error;
        reject(error);
      });

  const call = reCall
    ? reCall
    : (reactive({
        url,
        body,
        loading: true,
        data: undefined,
        response: undefined,
        error: undefined,
        errors: undefined,
        failed: false,
        then: then_,
        catch: catch_,
        reload: () => getCall(url, req, body, call),
      }) as Reactive<Call<T>>);

  if (reCall) {
    reCall.loading = true;
    reCall.failed = false;
    reCall.response = undefined;
    reCall.errors = undefined;
    reCall.error = undefined;
    // reCall.data = undefined;
    Object.assign(reCall, {
      then: then_,
      catch: catch_,
    });
    return reCall;
  }

  return call;
}

function getError(call: Call): Error {
  if (!call.failed) {
    return new Error(ui("Something went wrong"));
  }

  if (call.response?.status === 404) {
    return new Error(ui("Requested resource was not found"));
  }

  if (call.response?.status === 401) {
    return new Error(ui("You are not authorized to access this resource"));
  }

  return new Error(ui("Something went wrong"));
}

function areErrors(errors: any): errors is ServerError[] {
  return (
    errors instanceof Array &&
    errors.every(
      (e) => typeof e?.type === "string" && typeof e?.exception === "string"
    )
  );
}

function logErrors(errors: any, method: string) {
  if (!window.LOG_ERRORS) return;
  console.groupCollapsed(`%cServer Error [${method}]`, "color: red");
  if (areErrors(errors)) {
    errors.forEach((e) => console.error(e.exception));
  } else {
    console.error(errors);
  }
  console.groupEnd();
}

function getHeaders() {
  const headers: HeadersInit = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "X-Frappe-Site-Name": window.location.hostname,
  };

  // TODO: Review this logic
  if (window.csrf_token && window.csrf_token !== "{{ csrf_token }}") {
    headers["X-Frappe-CSRF-Token"] = window.csrf_token;
  }

  return headers;
}

function getParams(params?: Record<string, unknown>): string {
  if (!params) return "";
  if (Object.keys(params).length === 0) return "";

  const _params = new URLSearchParams();

  // Convert all values to strings
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === "string") {
      _params.append(key, value);
    }

    _params.append(key, JSON.stringify(value));
  }

  return `?${_params.toString()}`;
}

function getIndicator(data: unknown) {
  if (Array.isArray(data)) return `[${data.length} items]`;
  if (typeof data === "object" && data !== null)
    return `[${Object.keys(data).length} keys]`;
  return `[${typeof data}]`;
}

function logNonError(error: unknown) {
  console.groupCollapsed("%cClient Error", "color: red");
  console.error("Client Error", error);
  console.groupEnd();
}
