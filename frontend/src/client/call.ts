/**
 * TODO:
 * - add some tests for the new Call class to check if it works as expected
 * - add config, auto, cache, key (body if not set), ttl (invalidate on retrieval not settimeout), etc
 */
import { reactive, toRaw } from "vue";
import type { CallArgs, CallAPIArgs, Config, ServerError } from "./types";

export function call<Args extends any = unknown, Return extends any = unknown>(
  url: string,
  args?: CallArgs,
  config?: Config
): Call<Args, Return> {
  const method = args?.method ?? "POST";
  const body = args?.body;
  const params = args?.params;

  return new Call(method, url, body, params, config, false);
}

/**
 * Raw call to legacy FF API, used as a fallback when v2 doesn't work as expected.
 * Used only for calls to Framework defined endpoints.
 */
export function callV1<
  Args extends any = unknown,
  Return extends any = unknown
>({ method, path, body, params, config }: CallAPIArgs): Call<Args, Return> {
  const url = ["/api", path].join("/");
  return new Call(method, url, body, params, config, true);
}

/**
 * Raw call to FF API v2: https://github.com/frappe/frappe/pull/22300. This is
 * not meant to be used by itself but through the `api.path.method()` way.
 *
 * Returns a Reactive<Call> object.
 */

export function callV2<
  Args extends any = unknown,
  Return extends any = unknown
>({ method, path, body, params, config }: CallAPIArgs): Call<Args, Return> {
  const url = ["/api/v2", path].join("/");
  return new Call(method, url, body, params, config, true);
}

export class Call<Args extends any = unknown, Return extends any = unknown> {
  private url: string;
  private body?: string;
  private params?: string;
  private method: string;
  private _promise?: Promise<Return>;

  private _data?: Return;
  private _loading: boolean;
  private _failed: boolean;
  private _response?: Response;
  private _errors?: ServerError[];
  private _config?: Config;
  private _alloRerun?: boolean;
  private _isFFCall: boolean;

  constructor(
    method: string,
    url: string,
    body: Record<string, unknown> | undefined,
    params: Record<string, unknown> | undefined,
    config: Config | undefined,
    isFFCall: boolean
  ) {
    this.method = method;
    this.url = url;
    this.body = body ? JSON.stringify(body) : undefined;
    this.params = params ? getParams(params) : undefined;

    this._promise = undefined;
    this._loading = false;
    this._failed = false;
    this._response = undefined;
    this._errors = undefined;
    this._config = config;
    this._isFFCall = isFFCall;

    // TODO: check if this is fine
    const obj = reactive(this) as any as Call<Args, Return>;
    if (this._config?.auto !== false) {
      obj.run();
    }

    return obj;
  }

  get data() {
    return this._data;
  }

  get loading() {
    return this._loading;
  }

  get failed() {
    return this._failed;
  }

  get promise() {
    return this._promise;
  }

  get response() {
    return this._response;
  }

  get errors() {
    return this._errors;
  }

  run() {
    // Run with the same args
    return this._execute();
  }

  rerun(args?: Args) {
    if (!this._alloRerun) throw new Error("Rerun not allowed");

    // Update args before running
    this.reset();
    this.body = args ? JSON.stringify(args) : undefined;
    return this._execute();
  }

  then(resolve: (value: unknown) => void, reject?: (reason: unknown) => void) {
    const promise = this._execute();
    promise.then((res) => resolve(res)).catch((err) => reject?.(err));
    return promise;
  }

  catch(reject: (reason: unknown) => void) {
    const promise = this._execute();
    promise.catch((err) => reject(err));
    return promise;
  }

  private _execute(): Promise<Return> {
    if (this._promise) {
      return this._promise;
    }

    const promise = this.__execute();
    this._promise = promise;
    return promise;
  }

  private async __execute(): Promise<Return> {
    const start = performance.now();
    this._loading = true;
    const request: RequestInit = {
      method: this.method,
      body: this.body,
      headers: getHeaders(),
    };

    let data: Return;
    try {
      const url = [encodeURI(this.url), this.params].join("");
      const res = await fetch(url, request);
      this._response = res;
      this._failed = !res.ok;

      const json = await res.json();
      if (this._isFFCall) {
        data = json.data ?? json.message;
      } else {
        data = json;
      }

      this._data = data;
      if (this._failed && this._isFFCall) {
        this._errors = json?.errors;
      }
    } catch (err) {
      this._failed = true;
      throw err;
    } finally {
      this._loading = false;
      log(performance.now() - start, this);
    }

    return data;
  }

  private reset() {
    this._promise = undefined;
    this._data = undefined;
    this._loading = false;
    this._failed = false;
    this._response = undefined;
    this._errors = undefined;
  }
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

function log(duration: number, call: Call) {
  if (call.failed) {
    window.LOG_ERRORS && logErrors(call);
  } else {
    window.DEBUG_API && logResponse(duration, call);
  }
}

function logResponse(duration: number, call: Call) {
  const url = formatUrl(call.response?.url ?? "");
  const indicator = getIndicator(call.data);
  console.groupCollapsed(
    `%cAPI Response [${url}] ${indicator}`,
    "color: lightgreen"
  );
  console.log("Duration", duration, "ms");
  console.log("Data", toRaw(call.data));
  console.groupEnd();
}

function logErrors(call: Call) {
  console.groupCollapsed(
    `%cServer Error [${call.response?.url}]`,
    "color: red"
  );
  if (areErrors(call.errors)) {
    call.errors.forEach((e) => console.error(e.exception));
  } else {
    console.error(call.errors);
  }
  console.groupEnd();
}

function logNonError(error: unknown) {
  console.groupCollapsed("%cClient Error", "color: red");
  console.error("Client Error", error);
  console.groupEnd();
}

function getError(call: Call): Error {
  if (!call.failed) {
    return new Error("Something went wrong");
  }

  if (call.response?.status === 404) {
    return new Error("Requested resource was not found");
  }

  if (call.response?.status === 401) {
    return new Error("You are not authorized to access this resource");
  }

  return new Error("Something went wrong");
}

function areErrors(errors: any): errors is ServerError[] {
  return (
    errors instanceof Array &&
    errors.every(
      (e) => typeof e?.type === "string" && typeof e?.exception === "string"
    )
  );
}

function getIndicator(data: unknown) {
  if (Array.isArray(data)) return `[${data.length} items]`;
  if (typeof data === "object" && data !== null)
    return `[${Object.keys(data).length} keys]`;
  return `[${typeof data}]`;
}

function formatUrl(url: string) {
  const u = new URL(url);
  if (u.pathname.startsWith("/api/v2/method/")) {
    return u.pathname.slice(15);
  }

  return u.pathname;
}
