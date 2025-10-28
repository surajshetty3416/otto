import type {
  Content,
  ContentChunk,
  Meta,
  SessionItem,
} from "@/client/generated.types";
import { assert, isEqual } from "@/utils";
import type { ChunkContent, StreamContext } from "./types";
import type { InjectionKey, Ref } from "vue";

export const streamContextKey = Symbol("streamContext") as InjectionKey<
  Ref<null | StreamContext>
>;

export const sessionItemKey = Symbol(
  "sessionItem"
) as InjectionKey<SessionItem>;

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
  console.log(isNew, item);
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

    if (content.type !== targetContent.type) {
      target.content[i] = content;
      continue;
    }

    if ((isEqual(targetContent, content), 2)) continue;

    for (const key in content) {
      targetContent[key as keyof Content] = content[key as keyof Content];
    }
  }
}

function getItem(id: string, messages: SessionItem[]) {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].id === id) return messages[i];
  }

  return null;
}
