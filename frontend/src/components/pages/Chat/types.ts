import type { TextContent, ThinkingContent, ToolUseContent } from "@/client/generated.types";

export type ChunkContent = TextContent | ThinkingContent | ToolUseContent;
export interface StreamContext {
  itemId: string;
  chunkType: string;
}
