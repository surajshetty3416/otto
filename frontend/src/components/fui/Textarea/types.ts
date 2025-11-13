export interface TextareaProps {
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "subtle" | "outline";
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  debounce?: number;
  rows?: number;
  label?: string;
}
