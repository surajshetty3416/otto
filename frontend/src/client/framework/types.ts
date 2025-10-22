import type { OttoDocTypes } from "../generated.types";

export type GetListReturn<
  DocType extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[DocType] & string
> = Pick<OttoDocTypes[DocType], Field>[];

export type GetListArgs<
  Doc extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[Doc] & string
> = {
  doctype: Doc;
  fields: Field[];
  start?: number;
  page_length?: number;
  filters?: Record<string, unknown>;
  or_filters?: Record<string, unknown>;
  order_by?: `${Field} ${"asc" | "desc"}`;
};
