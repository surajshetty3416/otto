/**
 * TODO:
 * - add some tests for the new Call class to check if it works as expected
 * - add config, auto, cache, key (body if not set), ttl (invalidate on retrieval not settimeout), etc, onsuccess, onerror, etc
 */
import { reactive, toRaw } from "vue";
import type { CallArgs, CallAPIArgs, Config, ServerException } from "./types";

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
  private _error?: unknown;
  private _exception?: ServerException;
  private _config?: Config;
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
    this._error = undefined;
    this._exception = undefined;
    this._config = config;
    this._isFFCall = isFFCall;

    const obj = reactive(this) as any as Call<Args, Return>;
    if (this._config?.auto !== false) obj.run();

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

  get exception() {
    return this._exception;
  }

  get error() {
    return this._error;
  }

  run() {
    // Run with the same args, returns saved result
    return this._execute();
  }

  rerun(args?: Args) {
    // Update args before running
    this._reset();
    this.body = args ? JSON.stringify(args) : undefined;
    return this._execute();
  }

  then(resolve: (value: Return) => void, reject?: (reason: unknown) => void) {
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

    const promise = this.__execute().catch((error) => {
      this._setClientError(error);
      throw error;
    });

    this._promise = promise;
    return promise;
  }

  private async __execute(): Promise<Return> {
    window.DEBUG_API && logCall(this.url, this.body, this.params, this.method);

    const start = performance.now();
    this._loading = true;
    const request: RequestInit = {
      method: this.method,
      body: this.body,
      headers: getHeaders(this._isFFCall),
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
        this._exception = getError(json);
      }
    } catch (error) {
      this._setClientError(error);
      throw error;
    } finally {
      this._loading = false;
      logResponse(this, this.method, performance.now() - start);
    }

    return data;
  }

  private _setClientError(error: unknown) {
    this._failed = true;
    this._error = error;
    window.LOG_ERRORS && logClientError(this.url, this.method, error);
  }

  private _reset() {
    this._promise = undefined;
    this._data = undefined;
    this._loading = false;
    this._failed = false;
    this._response = undefined;
    this._exception = undefined;
    this._error = undefined;
  }
}

function getHeaders(isFFCall: boolean) {
  const headers: HeadersInit = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
  };

  if (isFFCall) {
    headers["X-Frappe-Site-Name"] = window.location.hostname;
  }

  // TODO: Review this logic
  if (
    isFFCall &&
    window.csrf_token &&
    window.csrf_token !== "{{ csrf_token }}"
  ) {
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

function logCall(
  url: string,
  body: string | undefined,
  params: string | undefined,
  method: string
) {
  const _url = formatUrl(url);
  console.groupCollapsed(`%cAPI Call [${method} ${_url}]`, "color: lightblue");
  try {
    console.log(body ?? JSON.parse(body ?? "{}"));
    params && console.log(params);
  } catch {
    console.log(body);
    params && console.log(params);
  }
  console.groupEnd();
}

function logClientError(url: string, method: string, error: unknown) {
  const _url = formatUrl(url);
  console.groupCollapsed(`%cClient Error [${method} ${_url}]`, "color: red");
  console.error(error);
  console.groupEnd();
}

function logResponse(call: Call, method: string, duration: number) {
  if (call.failed) {
    window.LOG_ERRORS && _logServerError(call, method, duration);
  } else {
    window.DEBUG_API && _logResponse(call, method, duration);
  }
}

function _logResponse(call: Call, method: string, duration: number) {
  const url = formatUrl(call.response?.url ?? "");
  const indicator = getIndicator(call.data);
  console.groupCollapsed(
    `%cAPI Response [${method} ${url}] ${indicator}`,
    "color: lightgreen"
  );
  console.log(toRaw(call.data));
  console.log("Duration", duration, "ms");
  console.groupEnd();
}

function _logServerError(call: Call, method: string, duration: number) {
  const url = formatUrl(call.response?.url ?? "");
  console.groupCollapsed(`%cServer Error [${method} ${url}]`, "color: red");

  if (call.exception) {
    console.error(call.exception.type);
    console.error(call.exception.traceback);
  }

  console.log("Duration", duration, "ms");
  console.groupEnd();
}

function getIndicator(data: unknown) {
  if (Array.isArray(data)) return `[${data.length} items]`;
  if (typeof data === "object" && data !== null)
    return `[${Object.keys(data).length} keys]`;
  return `[${typeof data}]`;
}

function getError(data: any): ServerException | undefined {
  if (isV2Error(data))
    return { type: data.errors[0].type, traceback: data.errors[0].exception };
  if (!isV1Error(data)) return undefined;

  let { exc_type, exception } = data;
  try {
    const lines = JSON.parse(exception as string);
    exception = lines.join("\n");
  } catch {}

  return { type: exc_type, traceback: exception };
}

function isRecord(data: any): data is Record<string, unknown> {
  return typeof data === "object" && data !== null;
}

function isV1Error(data: any): data is { exc_type: string; exception: string } {
  if (!isRecord(data)) return false;
  if (typeof data.exc_type !== "string") return false;
  if (typeof data.exception !== "string") return false;

  return true;
}

function isV2Error(
  data: any
): data is { errors: { type: string; exception: string }[] } {
  if (!isRecord(data)) return false;
  if (!Array.isArray(data.errors)) return false;
  return data.errors.every(
    (e) => typeof e?.type === "string" && typeof e?.exception === "string"
  );
}

function formatUrl(url: string) {
  let pathname = url;
  try {
    const u = new URL(url);
    pathname = u.pathname;
  } catch {}

  if (pathname.startsWith("/api/v2/method/otto.api")) {
    return decodeURI(pathname.slice(20));
  }

  if (pathname.startsWith("/api/v2/")) {
    return decodeURI(pathname.slice(8));
  }

  return decodeURI(pathname);
}
