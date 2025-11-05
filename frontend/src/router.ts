import { createRouter, createWebHistory } from "vue-router";

export const defaultRouteName = "Chat";
const routes = [
  {
    path: "/",
    name: "Desktop",
    component: () => import("./components/pages/Desktop.vue"),
    children: [
      {
        path: "chat/:chatId?",
        name: "Chat",
        component: () => import("./components/pages/Chat/Chat.vue"),
        props: true,
      },
    ],
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("./components/pages/Login.vue"),
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
