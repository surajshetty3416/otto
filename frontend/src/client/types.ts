import type { Reactive } from "vue";
import { framework } from "./framework";
import type { API as OttoAPI, OttoDocTypes } from "./generated.types";

export type ReactiveCall<T = unknown> = Reactive<Call<T>>;

export type GetList<
  DocType extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[DocType] & string
> = ReactiveCall<Pick<OttoDocTypes[DocType], Field>[]>;

export type ServerError = {
  type: string;
  exception: string;
};

export interface Modifier {
  // cache: boolean;
  // auto: boolean;
}

export interface Call<T = unknown> {
  url: string /** The API path that is being called */;
  body?: string /**JSON used here to prevent gc of mutable objects */;
  loading: boolean /** Is true until the response promise resolves */;
  data?: T /** Set only once the promise resolves */;
  failed: boolean /** Set if fetch errored out */;
  response?: Response /** Response object from the fetch call */;

  /**
   * Note: these error fields are not for userfacing UI, if an
   * error occurs then the userfacing message should be defined
   * client side depending on the action being called.
   *
   * If an error occurs server side and data about the raw error has
   * to be sent, the error should be handled and the data should be
   * sent instead.
   */
  error?: Error /** Set when the error occurs client side */;
  errors?: ServerError[] /** Set when the error occurs server side */;

  /**
   * Methods that make a Call behave like a Promise.
   */
  then(resolve: (value: T) => any, reject?: (reason: any) => any): void;
  reload(): Reactive<Call<T>>;
}

export type API = typeof framework & _API<OttoAPI>;

/**
 * API conversion types to convert the raw API to the form used by the client.
 */

type RawFunction = (args: any) => any;

export type APIFunction<RF extends RawFunction> =
  Parameters<RF>[0] extends undefined
    ? (args?: null | undefined, modifier?: Modifier) => Call<ReturnType<RF>>
    : (args: Parameters<RF>[0], modifier?: Modifier) => Call<ReturnType<RF>>;

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
