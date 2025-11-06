/* Check `./README.md` for information. */

import { api } from "./api";

export { api, framework } from "./api";
export { call } from "./call";

/**
 * Common API calls used around the UI
 */
export const get_user = api.get_user();
export const get_user_info = api.get_user_info();
export const list_chats = api.chat.list_chats(null, { cache: true });
export const list_assistants = api.chat.list_assistants(null, { cache: true });
export const list_models = api.chat.list_models(null, { cache: true });
