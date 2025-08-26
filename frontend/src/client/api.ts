import { markRaw } from "vue";
import { callAPIv2 } from "./call";
import { framework } from "./framework";
import type { API, Modifier } from "./types";

/**
 * The `api` object is used to call two kinds of APIs:
 * - APIs defined in Frappe Framework (using v1)
 * - APIs defined in Otto (using v2)
 *
 * All backend calls are made through this. Check `./README.md` for more
 * details.
 */
export const api = markRaw(
  new Proxy(
    {},
    {
      get(_, prop) {
        if (typeof prop !== "string")
          throw Error(
            `string expected instead of ${typeof prop} ${String(prop)}`
          );
        return getApi(prop);
      },
    }
  )
) as API;

function getApi(path: string, modifier?: Modifier): unknown {
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
      if (target.path) return getApi(`${target.path}.${prop}`, modifier);
      return getApi(`${prop}`, modifier);
    },
    apply(target, _, args) {
      if (window.DEBUG_API) {
        console.groupCollapsed(
          `%cAPI Call [${target.path}]`,
          "color: lightblue"
        );
        console.log("path", target.path);
        console.log("args", args);
        console.log("modifier", modifier);
        console.groupEnd();
      }

      if (target.path === "modify") {
        return getApi("", args[0]);
      }

      if (target.path in framework) {
        // @ts-expect-error
        return framework[target.path as keyof typeof framework](...args);
      }

      // TODO: Implement usage of modifiers like cache
      return callAPIv2(target.path, args[0]);
    },
  });

  return self;
}
