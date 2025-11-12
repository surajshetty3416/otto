import type { Call } from "./call";
import type { API as OttoAPI, OttoDocTypes } from "./generated.types";

export type GetListReturn<
  DocType extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[DocType] & string
> = Pick<OttoDocTypes[DocType], Field>[];

export type GetListOptions<Field extends string> = {
  start?: number;
  limit?: number;
  filters?: Record<string, unknown> | unknown[];
  or_filters?: Record<string, unknown>;
  order_by?: `${Field} ${"asc" | "desc"}`;
};

export interface CallArgs {
  method?: "GET" | "PUT" | "POST" | "DELETE";
  body?: Record<string, unknown>;
  params?: Record<string, unknown>;
}

export interface CallAPIArgs {
  method: "GET" | "PUT" | "POST" | "DELETE";
  path: string;
  body?: Record<string, unknown>;
  params?: Record<string, unknown>;
  config?: Config;
}

export type ServerException = {
  type: string;
  message?: string;
  traceback?: string;
};

export interface Config {
  ttl?: number; // seconds, if not set cache invalidate only on api response
  key?: string; // if not set, hash(url, method, body, params) is used
  auto?: boolean; // default true, if false then call is not executed

  /**
   * default false, if true then data is first fetched from the cache
   * and then the api is called to get the latest data.
   *
   * i.e. stale while revalidating; invalidated on data fetch
   */
  cache?: boolean; // default false, if true then cache is used

  /**
   * default false, needs cache: true
   *
   * If true, then call is executed only once and all subsequent calls are
   * return data from the cache without revalidating the data.
   * 
   * Can be invalidated with call.reset or by using useCache false when calling
   * run.
   * 
   * Should ideally be used by ttl, incase a page is not unloaded but the
   * backend data has changed.
   *
   * i.e. stale without revalidating; invalidated on page refresh
   */
  once?: boolean; // default false, if true then call is executed only once
  // signal?: AbortSignal; // if set, the call is aborted when the signal is aborted
}

export type API = _API<OttoAPI>;

/**
 * API conversion types to convert the raw API to the form used by the client.
 */

type RawFunction = (args: any) => any;

export type APIFunction<RF extends RawFunction> =
  Parameters<RF>[0] extends undefined
    ? (
        args?: null | undefined,
        config?: Config
      ) => Call<undefined, ReturnType<RF>>
    : (
        args: Parameters<RF>[0],
        config?: Config
      ) => Call<Parameters<RF>[0], ReturnType<RF>>;

export type _API<Raw> = {
  [K in keyof Raw]: Raw[K] extends RawFunction
    ? APIFunction<Raw[K]>
    : Raw[K] extends Record<string, any>
    ? _API<Raw[K]>
    : never;
};

/**
 * Utility types to check if a type is a raw API or a raw function.
 */
export type CheckIsRawFunction<X> = X extends RawFunction ? true : false;
export type CheckIsRawAPI<X> = X extends RawFunction
  ? CheckIsRawFunction<X> extends true
    ? true
    : false
  : X extends object
  ? {
      [K in keyof X]: CheckIsRawAPI<X[K]>;
    }[keyof X] extends true
    ? true
    : false
  : false;
export type AssertTrue<T extends true> = T;
export type CallData<T> = T extends Call<infer U> ? U : T;
