import type { IconName } from "../types";

export type ToastPosition =
  | "top-right"
  | "top-center"
  | "top-left"
  | "bottom-right"
  | "bottom-center"
  | "bottom-left";

export interface ToastProps {
  position?: ToastPosition;
  icon?: IconName;
  iconClasses?: string;
  title?: string;
  message?: string;
  duration?: number;
  type?: "info" | "success" | "warning" | "error";
}
