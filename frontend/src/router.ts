import { createRouter, createWebHistory } from "vue-router";
// import Chat from "./components/pages/Chat/Chat.vue";
import Desktop from "./components/pages/Desktop.vue";
import Login from "./components/pages/Login.vue";
import { isLoggedIn, toLogin } from "./client/utils";

export const defaultRouteName = "Chat";
const routes = [
  {
    path: "/",
    name: "Desktop",
    component: Desktop,
    children: [
      // {
      //   path: "chat",
      //   name: "Chat",
      //   component: Chat,
      // },
    ],
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
  },
];

const base = import.meta.hot ? "/" : "/otto";
const history = createWebHistory(base);
const router = createRouter({ history, routes });

router.beforeEach(async (to, _from, next) => {
  const loggedIn = await isLoggedIn();
  const sendToDefault = ["Login", "Desktop", undefined].includes(
    to.name as string
  );

  if (loggedIn && sendToDefault) {
    return next({ name: defaultRouteName });
  }

  if (loggedIn || to.name === "Login") {
    return next();
  }

  if (import.meta.hot) {
    return next({ name: "Login" });
  }

  toLogin();
  return false;
});

export default router;
