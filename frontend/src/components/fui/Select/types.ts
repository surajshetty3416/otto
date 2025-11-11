import type { OttoDocTypes } from "@/client/generated.types";

type SelectOption =
  | string
  | {
      label: string;
      value: string;
      disabled?: boolean;
    };

export interface SelectProps {
  size?: "sm" | "md" | "lg";
  variant?: "subtle" | "outline" | "ghost";
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  options?: SelectOption[];
  /**
   * Use fetched field meta to populate options, help-text, etc.
   */
  doctype?: keyof OttoDocTypes;
  fieldname?: string;
  label?: string;
  showLabel?: boolean; // if fetching from meta
  description?: string;
  showDescription?: boolean; // if fetching from meta
}
