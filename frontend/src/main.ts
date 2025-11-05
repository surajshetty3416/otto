import { createApp } from "vue";
import App from "./App.vue";
import { api, framework } from "./client";
import { useGlobals } from "./globals";
import router from "./router";
import "./style.css";
import { watcher } from "./client/watcher";
import { toLogin } from "./client/utils";

setIsDevMode();
function initApp() {
  const app = createApp(App);

  app.use(router);
  app.config.globalProperties.$g = useGlobals();

  app.mount("#app");
  return app;
}

const app = initApp();

window.LOG_ERRORS = true;
if (window.is_dev_mode) {
  window.DEBUG_API = true;
  window.api = api;
  window.framework = framework;
  window.globals = app.config.globalProperties.$g;
}

function setIsDevMode() {
  const vals: unknown[] = ["true", "{{ is_dev_mode }}", true, 1, "True"];
  if (vals.includes(window.is_dev_mode)) {
    window.is_dev_mode = true;
  } else {
    window.is_dev_mode = false;
  }
}

watcher.add(
  () => {
    console.log(router.currentRoute.value.name);
    console.log(router.currentRoute.value);
    if (router.currentRoute.value.name === "Login") return;
    toLogin();
  },
  { status: 403 }
);
