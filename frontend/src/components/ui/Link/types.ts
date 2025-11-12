import type { OttoDocTypes } from "@/client/generated.types";

export type LinkOption = {
  label: string;
  value: string;
  disabled?: boolean;
  item?: Record<string, unknown>;
};

export interface LinkProps {
  /**
   * For fallthrough props, see ComboboxProps
   * Use fetched field meta to populate options, help-text, etc.
   */
  doctype: keyof OttoDocTypes; // doctype of whose Link field should be fetched
  fieldname: string; // fieldname of the Link field in `doctype`
  fields?: string[]; // additional fields of the Link option to fetch for transforms
  transform?: (option: LinkOption) => LinkOption;
}
