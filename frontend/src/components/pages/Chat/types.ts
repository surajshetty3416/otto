import type {
  RealtimeChatMessage,
  TextContent,
  ThinkingContent,
  ToolUseContent,
} from "@/client/generated.types";

export type ChunkContent = TextContent | ThinkingContent | ToolUseContent;
export interface StreamContext {
  chunks: RealtimeChatMessage[];
  isStreamingResponse: boolean;
}
