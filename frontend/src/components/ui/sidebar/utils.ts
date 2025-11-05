import { LocalStore } from "@/components/store";
import type { SidebarState } from "./types";

export const sidebarState = new LocalStore<SidebarState>("sidebar-state");
