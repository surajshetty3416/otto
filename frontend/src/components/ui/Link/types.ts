import type { OttoDocTypes } from "@/client/generated.types";

export type LinkOption = {
  label: string;
  value: string;
  disabled?: boolean;
  item: Record<string, unknown>;
};

export interface LinkProps {
  size?: "xs" | "sm" | "md" | "lg";
  variant?: "subtle" | "outline" | "ghost";
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  /**
   * Use fetched field meta to populate options, help-text, etc.
   */
  doctype: keyof OttoDocTypes;
  fieldname: string;
  containerClass?: string;
}
