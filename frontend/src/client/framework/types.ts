import type { OttoDocTypes } from "../generated.types";

export type GetListReturn<
  DocType extends keyof OttoDocTypes,
  Field extends keyof OttoDocTypes[DocType] & string
> = Pick<OttoDocTypes[DocType], Field>[];
