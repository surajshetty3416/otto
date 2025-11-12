import type { OttoDocTypes } from "@/client/generated.types";
import type { ComboboxOption } from "../combobox/types";

export interface SelectProps {
  options?: ComboboxOption[];
  /**
   * Use fetched field meta to populate options, help-text, etc.
   */
  doctype?: keyof OttoDocTypes;
  fieldname?: string;
  containerClass?: string;
}
