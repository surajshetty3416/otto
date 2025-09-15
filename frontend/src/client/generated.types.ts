import type { Call } from "./types";

export interface DocTypes {}

// Not currently generated, but should be
export interface API {
  get_user(): Call<Record<string, string>>;
  ping(): Call<string>;
  chat: {
    test(): Call<string>;
    chat(args: { query: string }): Call<Record<string, string>>;
  };
}
