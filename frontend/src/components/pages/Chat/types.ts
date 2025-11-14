import type {
  TextContent,
  ThinkingContent,
  ToolUseContent
} from "@/client/generated.types";

export type ChunkContent = TextContent | ThinkingContent | ToolUseContent;

export interface ChatState {
  [key: `chat::${string}`]: string;
}
