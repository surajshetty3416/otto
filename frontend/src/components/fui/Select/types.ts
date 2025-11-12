import type { OttoDocTypes } from "@/client/generated.types";

type SelectOption =
  | string
  | {
      label: string;
      value: string;
      disabled?: boolean;
    };

export interface SelectProps {
  size?: "xs" | "sm" | "md" | "lg";
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
  containerClass?: string;
}
