import type {
  RealtimeChatMessage,
  TextContent,
  ThinkingContent,
  ToolUseContent,
} from "@/client/generated.types";

export type ChunkContent = TextContent | ThinkingContent | ToolUseContent;
export interface StreamContext {
  messages: RealtimeChatMessage[];
  isStreamingResponse: boolean;
}

export interface ChatState {
  [key: `chat::${string}`]: string;
}
