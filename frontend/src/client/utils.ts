import router from "../router";
import type { RealtimeChatMessage } from "./generated.types";

export function toLogin(useRedirect: boolean = true) {
  /**
   * When running in Vite dev mode with HMR, Otto's login page is used.
   * This is cause they're served from different servers to different
   * addresses and so the context is not shared.
   *
   * When the source is built and served by Frappe, it's being served
   * from the same host and so the framework login page can be used.
   */
  if (import.meta.hot) {
    router.push({ name: "Login" });
  } else {
    const currentPath = encodeURIComponent(window.location.pathname);
    let href = `/login`;
    if (useRedirect) {
      href += `?redirect-to=${currentPath}`;
    }

    window.location.href = href;
  }
}

export function hash(value: string, seed: number = 0): number {
  // Stolen from: https://stackoverflow.com/a/52171480
  let h1 = 0xdeadbeef ^ seed,
    h2 = 0x41c6ce57 ^ seed;
  for (let i = 0, ch; i < value.length; i++) {
    ch = value.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507);
  h1 ^= Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507);
  h2 ^= Math.imul(h1 ^ (h1 >>> 13), 3266489909);

  return 4294967296 * (2097151 & h2) + (h1 >>> 0);
}

export function logRealtime(message: RealtimeChatMessage) {
  let m = `%cRealtime [${message.type}]`;
  if (message.type === "chunk") {
    m += ` [${message.data.type} ${message.data.message}]`;
  }

  if (message.type === "log" && typeof message.data === "string") {
    m += ` ${message.data}`;
  }

  let style = "color: lightyellow";
  if (message.type === "error") style = "color: red";
  if (message.type === "request") style = "color: orange";
  if (message.type === "request-acknowledge") style = "color: plum";
  if (message.type === "tool-execution-update") style = "color: turquoise";
  if (message.type === "item") style = "color: aquamarine";
  if (message.type === "pong") style = "color: gray";
  if (message.type === "log") style = "color: olive";
  if (message.type === "chunk" && message.data.type !== "system")
    style = "color: gray";

  console.groupCollapsed(m, style);
  console.log(message.data);
  if ("chat_id" in message) console.log("chat_id:", message.chat_id);
  if ("timestamp" in message)
    console.log("timestamp:", new Date(message.timestamp));
  if ("traceback" in message && message.traceback)
    console.log(message.traceback);
  if ("more" in message && message.more) console.log(message.more);
  console.log("id:", message.id);
  console.groupEnd();
}

// Use to log unexpected states or errors that should not happen
export function logError(
  title: string,
  error?: unknown,
  context?: Record<string, unknown>
) {
  console.groupCollapsed(`%cError [${title}]`, "color: red");
  if (context) {
    console.log("context:");
    console.log(JSON.stringify(context, null, 2));
  }

  if (typeof error !== "undefined" && error !== null) console.error(error);
  console.groupEnd();
}
