import type { API } from "./client";
import type { Globals } from "./types";

declare module "vue" {
  interface ComponentCustomProperties {
    $g: Globals;
  }
}

declare global {
  interface Window {
    DEBUG_API?: boolean;
    LOG_ERRORS?: boolean;
    csrf_token?: string;
    site_name?: string;
    globals?: Globals;
    api?: API;
    is_dev_mode?: boolean;
  }
}
