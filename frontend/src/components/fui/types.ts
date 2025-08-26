import type { icons } from "lucide-vue-next";
import type { ButtonProps } from "./Button/types";

export type IconName = keyof typeof icons;

export interface CheckboxProps {
  size?: "sm" | "md";
  label?: string;
  checked?: boolean;
  disabled?: boolean;
  padding?: boolean;
  modelValue?: boolean | 1 | 0;
  id?: string;
}

export interface TextInputProps {
  label?: string;
  type?: TextInputTypes;
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "subtle" | "outline";
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  modelValue?: string | number;
  debounce?: number;
  required?: boolean;
}

export type TextInputTypes =
  | "date"
  | "datetime-local"
  | "email"
  | "file"
  | "month"
  | "number"
  | "password"
  | "search"
  | "tel"
  | "text"
  | "time"
  | "url"
  | "week"
  | "range";

export interface TextareaProps {
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "subtle" | "outline";
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  modelValue?: string;
  debounce?: number;
  rows?: number;
  label?: string;
}

export type DialogIcon = {
  name: IconName;
  appearance?: "warning" | "info" | "danger" | "success";
};

export type DialogOptions = {
  title?: string;
  message?: string;
  // default size = 'lg'
  size?:
    | "xs"
    | "sm"
    | "md"
    | "lg"
    | "xl"
    | "2xl"
    | "3xl"
    | "4xl"
    | "5xl"
    | "6xl"
    | "7xl";
  icon?: DialogIcon | IconName;
  actions?: Array<DialogAction>;
  // default position = 'center'
  position?: "top" | "center";
};

type DialogActionContext = {
  close: () => void;
};

type DialogAction = ButtonProps & {
  onClick?: (context: DialogActionContext) => any | Promise<any>;
};

export interface DialogProps {
  modelValue: boolean;
  options?: DialogOptions;
  disableOutsideClickToClose?: boolean;
}
