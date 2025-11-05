import type {
  Assistant,
  ListChatItem,
  ModelDetails,
} from "@/client/generated.types";
import type { Component } from "vue";

export interface SidebarItem {
  name: string;
  icon: Component;
  route?: string; // used with vue router
  href?: string; // used with a element
}

export interface ChatListItem extends ListChatItem {
  model?: ModelDetails;
  assistant_?: Assistant;
}

export interface SidebarState {
  isCollapsed: boolean;
  isChatListOpen: boolean;
}
