export type ComboboxOption = {
  label: string;
  value: string;
  disabled?: boolean;
  item?: Record<string, unknown>;
};

export interface ComboboxProps {
  size?: "xs" | "sm" | "md" | "lg";
  variant?: "subtle" | "outline" | "ghost";
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  options: ComboboxOption[];
  showSearch?: boolean;
}
