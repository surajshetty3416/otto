import { useGlobals } from "../globals";
import router from "../router";
import { api } from "./api";

export async function isLoggedIn(force: boolean = false) {
  const globals = useGlobals();

  // Optimistically return true if user is already logged in
  // If not logged in, then route to login
  if (globals.user && !force) {
    isLoggedIn(true).catch(() => toLogin());
    return true;
  }

  try {
    globals.user = (await api.get_user()).user;
    return true;
  } catch {
    globals.user = undefined;
    return false;
  }
}

export function toLogin() {
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
    window.location.href = `/login?redirect-to=${currentPath}`;
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
