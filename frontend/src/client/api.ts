import { markRaw } from "vue";
import { callV2 } from "./call";
import { handlers as frameworkHandlers } from "./framework";
import type { API } from "./types";

/**
 * The `api` object is used to call APIs defined in Otto (using v2).
 */
export const api = getApi() as API;

/**
 * The `framework` object is used to call APIs defined in Frappe Framework (using v1 & v2).
 */
export const framework = getApi() as typeof frameworkHandlers;

function getApi() {
  const api = new Proxy(
    {},
    {
      get(_, prop) {
        if (typeof prop !== "string")
          throw Error(
            `string expected instead of ${typeof prop} ${String(prop)}`
          );
        return _getApi(prop);
      },
    }
  );
  return markRaw(api);
}

function _getApi(path: string): unknown {
  const a: { path: string; (): void } = function () {};
  a.path = path;

  const self = new Proxy(a, {
    get(target, prop) {
      if (typeof prop !== "string")
        throw Error(`string expected, got ${typeof prop} ${String(prop)}`);

      /**
       * Note: this is recursively called so that the target has some
       * sense of immutability, this is to allow such code:
       *
       * ```
       * const task = api.task;
       * await task.function_a();
       * await task.function_b();
       * ```
       */
      if (target.path) return _getApi(`${target.path}.${prop}`);
      return _getApi(`${prop}`);
    },
    apply(target, _, args) {
      if (target.path in frameworkHandlers) {
        const handler =
          frameworkHandlers[target.path as keyof typeof frameworkHandlers];

        // @ts-expect-error
        return handler(...args);
      }

      const path = `method/otto.api.${target.path}`;
      return callV2({
        method: "POST",
        path,
        body: args[0],
        params: undefined,
        config: args[1],
      });
    },
  });

  return self;
}
