import type { Reactive } from "vue";
import { framework } from "./framework";
import type { API as OttoAPI, DocTypes } from "./generated.types";

export type ReactiveCall<T = unknown> = Reactive<Call<T>>;

export type GetList<
  DocType extends keyof DocTypes,
  Field extends keyof DocTypes[DocType] & string
> = ReactiveCall<Pick<DocTypes[DocType], Field>[]>;

export type ServerError = {
  type: string;
  exception: string;
};

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

export interface Modifier {
  cache?: boolean | string | string[];
}

export type API = typeof framework &
  OttoAPI & { modify(modifier: Modifier): typeof framework & OttoAPI };

export type CallData<T> = T extends Call<infer U> ? U : T;
