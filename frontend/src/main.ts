import { createApp } from "vue";
import App from "./App.vue";
import { api } from "./client";
import { useGlobals } from "./globals";
import router from "./router";
import "./style.css";

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
