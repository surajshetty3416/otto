import type {
  Assistant,
  Content,
  ContentChunk,
  Meta,
  PendingRequest,
  RealtimeChatMessage,
  SessionItem,
  ToolConfig,
  ToolUseContent,
  ToolUseUpdate,
} from "@/client/generated.types";
import { assert, isEqual } from "@/utils";
import type { InjectionKey, Ref } from "vue";
import type { ChunkContent, StreamContext } from "./types";
import { Bot, Brain, Zap } from "lucide-vue-next";
import { models } from "@/common";
import { api } from "@/client";

export const save_settings = api.chat.save_settings(
  { chat_id: "", settings: undefined },
  { auto: false }
);

export const streamContextKey = Symbol(
  "streamContext"
) as InjectionKey<StreamContext>;

export const sessionItemKey = Symbol(
  "sessionItem"
) as InjectionKey<SessionItem>;

export const toolConfigKey = Symbol("toolConfig") as InjectionKey<
  Ref<Record<string, ToolConfig>>
>;

export const pendingRequestsKey = Symbol("pendingRequests") as InjectionKey<
  Record<string, PendingRequest>
>;

export function getUserSessionItem(query: string): SessionItem {
  return {
    id: "",
    content: [{ type: "text", text: query }],
    next: [],
    selected_next: 0,
    meta: {
      role: "user",
      model: null,
      input_tokens: 0,
      output_tokens: 0,
      cost: 0,
      timestamp: Date.now(),
      start_time: 0,
      end_time: 0,
      end_reason: null,
      time_to_first_chunk: 0,
      inter_chunk_latency: 0,
    },
  };
}

export function getAgentSessionItem(id: string): SessionItem {
  return {
    id,
    content: [],
    next: [],
    selected_next: 0,
    meta: {
      role: "agent",
      model: "",
      input_tokens: 0,
      output_tokens: 0,
      cost: 0,
      timestamp: Date.now(),
      start_time: 0,
      end_time: 0,
      end_reason: null,
      time_to_first_chunk: 0,
      inter_chunk_latency: 0,
    },
  };
}
function updateItemWithChunk(item: SessionItem, chunk: ContentChunk) {
  assert(chunk.type !== "system", "system chunk should not be updated");

  let isNew = false;
  let content: Content | undefined = item.content.at(-1);
  if (!content || content?.type !== chunk.type) {
    content = getContentFromChunkType(chunk.type);
    isNew = true;
  }

  updateContent(content, chunk);

  if (isNew) {
    item.content.push(content);
  }
}

function updateContent(content: Content, chunk: ContentChunk) {
  switch (chunk.type) {
    case "text":
      assert(content.type === "text", "content must be a text content");
      content.text += chunk.content;
      break;
    case "thinking":
      assert(content.type === "thinking", "content must be a text content");
      content.text += chunk.content;
      break;
    case "tool_use":
      assert(content.type === "tool_use", "content must be a tool use content");
      content.name = chunk.content.name || content.name;
      content.id = chunk.content.id || content.id;

      /**
       * _args aren't actually used as of now, once the stream completes
       * a final item is sent with the complete args, this is used directly
       *
       * in the case of multiple tool calls the _args object may be used to
       * show once a ToolUseContent has been generated completely.
       */

      if (typeof content._args !== "string") content._args = "";
      if (typeof chunk.content.args === "string") {
        content._args += chunk.content.args;
      }
      break;
  }
}

function getContentFromChunkType(
  chunkType: Exclude<ContentChunk["type"], "system">
): ChunkContent {
  switch (chunkType) {
    case "text":
      return { type: "text", text: "" };
    case "thinking":
      return { type: "thinking", text: "", signature: null };
    case "tool_use":
      return {
        type: "tool_use",
        id: "",
        name: "",
        status: "pending",
        result: null,
        args: {},
        _args: "",
        override: null,
        start_time: 0,
        end_time: 0,
        stdout: null,
        stderr: null,
      };
    default:
      // no-op
      throw new Error(`Unknown chunk type: ${chunkType}`);
  }
}

export function handleContentChunk(
  chunk: ContentChunk,
  messages: SessionItem[]
) {
  assert(chunk.type !== "system", "system chunk not handled here");

  let isNew = false;
  let item = getItem(chunk.item_id, messages);

  if (!item) {
    isNew = true;
    item = getAgentSessionItem(chunk.item_id);
  }

  updateItemWithChunk(item, chunk);
  if (isNew) messages.push(item);
}

export function handleItem(item: SessionItem, messages: SessionItem[]) {
  let prev = null;
  let target = null;

  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].id === item.id) target = messages[i];
    if (i - 1 >= 0) prev = messages[i - 1];
  }

  if (prev) {
    prev.next.push(item.id);
    prev.selected_next = prev.next.length - 1;
  }

  if (!target) {
    messages.push(item);
    return;
  }

  /**
   * Copy values over to prevent weird layout shifts
   */

  for (const key in item.meta) {
    // @ts-expect-error - not all can be null, should be safe
    target.meta[key as keyof Meta] = item.meta[key as keyof Meta];
  }

  for (let i = 0; i < item.content.length; i++) {
    const content = item.content[i];
    const targetContent = target.content[i];
    if (!targetContent) {
      if (target.content.length === i) target.content.push(content);
      else target.content[i] = content;
      continue;
    }

    if (content.type !== targetContent.type) {
      target.content[i] = content;
      continue;
    }

    if (isEqual(targetContent, content, 2)) continue;

    for (const key in content) {
      targetContent[key as keyof Content] = content[key as keyof Content];
    }
  }
}

export function handleToolUseUpdate(
  update: ToolUseUpdate,
  messages: SessionItem[]
) {
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i];
    for (const content of message.content) {
      if (content.type !== "tool_use" || content.id !== update.id) continue;

      content.status = update.is_error ? "error" : "success";
      content.stdout = update.stdout;
      content.stderr = update.stderr;
      content.start_time = update.start_time;
      content.end_time = update.end_time;

      let result = update.result;
      if (typeof result != "string") {
        try {
          result = JSON.stringify(result);
        } catch {
          result = String(result);
        }
      }

      assert(typeof result === "string", "type check");
      content.result = result;
    }
  }
}

export function getToolUseContent(
  toolUseId: string,
  messages: SessionItem[]
): ToolUseContent | null {
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i];
    for (const content of message.content) {
      if (content.type === "tool_use" && content.id === toolUseId) {
        return content;
      }
    }
  }
  return null;
}

export function updateStreamContext(
  message: RealtimeChatMessage,
  streamContext: StreamContext
) {
  /**
   * Stream context will maintain a contiguous stream of similar message chunks
   * it's mainly used for indicators and to update various UI elements as stream
   * changes.
   */
  if (message.type === "pong") return;

  if (message.type === "chunk" && message.data.type === "system") {
    switch (message.data.message) {
      case "start":
        streamContext.isStreamingResponse = true;
        break;
      case "end":
        streamContext.isStreamingResponse = false;
        break;
    }
    return;
  }

  if (streamContext.messages.at(0)?.type !== message.type) {
    streamContext.messages.length = 0;
  }

  if (streamContext.messages.length === 0) {
    streamContext.messages.push(message);
    return;
  }

  if (message.type !== "chunk" || message.data.type === "system") return;
  const last = streamContext.messages.at(-1)!;
  assert(last.type === "chunk", "type check");

  if (
    last.data.type !== message.data.type ||
    last.data.item_id !== message.data.item_id
  ) {
    streamContext.messages.length = 0;
  }

  streamContext.messages.push(message);

  /**
   * Update thinking and tool use content as stream changes
   * Update chat indicator to show sensible messages as stream changes
   */
}

function getItem(id: string, messages: SessionItem[]) {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].id === id) return messages[i];
  }

  return null;
}

export function getAssistantIcon(assistant: Assistant) {
  if (assistant.reasoning_effort) {
    return Brain;
  }

  const model = models.value[assistant.llm];
  if (["Very Small", "Small"].includes(model?.size ?? "")) {
    return Zap;
  }

  return Bot;
}
