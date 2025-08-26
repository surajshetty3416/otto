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
