import type { Call } from "./call";
import type { API as OttoAPI } from "./generated.types";

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

export type ServerError = {
  type: string;
  exception: string;
};

export interface Config {
  // cache: boolean;
  auto: boolean; // default true, if false then call is not executed
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
        modifier?: Config
      ) => Call<undefined, ReturnType<RF>>
    : (
        args: Parameters<RF>[0],
        modifier?: Config
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
