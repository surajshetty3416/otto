import type { Component } from "vue";

export interface SwitchProps {
  size?: "sm" | "md";
  label?: string;
  description?: string;
  disabled?: boolean;
  icon?: Component;
  labelClasses?: string;
}
