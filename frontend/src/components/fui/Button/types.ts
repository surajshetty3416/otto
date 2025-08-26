import type { Component } from "vue";
import type { RouteLocation } from "vue-router";

export type Theme = "gray" | "blue" | "green" | "red";
export type Size = "sm" | "md" | "lg" | "xl" | "2xl";
export type Variant = "solid" | "subtle" | "outline" | "ghost";

export interface ButtonProps {
  theme?: Theme;
  size?: Size;
  variant?: Variant;
  label?: string;
  icon?: string | Component;
  iconLeft?: string | Component;
  iconRight?: string | Component;
  loading?: boolean;
  loadingText?: string;
  disabled?: boolean;
  route?: RouteLocation;
  link?: string;
}
