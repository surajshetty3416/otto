import { createRouter, createWebHistory } from "vue-router";
import Chat from "./components/pages/Chat/Chat.vue";
import Desktop from "./components/pages/Desktop.vue";
import Login from "./components/pages/Login.vue";

export const defaultRouteName = "Chat";
const routes = [
  {
    path: "/",
    name: "Desktop",
    component: Desktop,
    children: [
      {
        path: "chat/:chatId?",
        name: "Chat",
        component: Chat,
        props: true,
      },
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

if (window.is_dev_mode) {
  // @ts-ignore
  window.router = router;
}

export default router;
