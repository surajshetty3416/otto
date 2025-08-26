import type { Call } from "./types";

export interface DocTypes {}

export interface API {
  get_user(): Call<Record<string, string>>;
  ping(): Call<string>;
}
