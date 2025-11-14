import type {
  ContentChunk,
  RealtimeChatMessage,
} from "@/client/generated.types";
import { logError } from "@/client/utils";
import { assert } from "@/utils";
import { reactive } from "vue";

type MessageType = RealtimeChatMessage["type"] | ContentChunk["type"];

const NOT_SET_YET = "not-set-yet";

export class StreamContext {
  messages: RealtimeChatMessage[];
  chatId: string;
  isWaiting: boolean;
  isStreamingResponse: boolean;

  constructor() {
    this.messages = [];
    this.chatId = NOT_SET_YET;
    this.isWaiting = false;
    this.isStreamingResponse = false;
    return reactive(this) as any as StreamContext;
  }

  waiting() {
    this.isWaiting = true;
  }

  set(chatId: string) {
    if (this.chatId !== NOT_SET_YET) this.reset();
    this.chatId = chatId;
  }

  reset(keepid: boolean = false) {
    if (!keepid) this.chatId = NOT_SET_YET;
    this.messages.length = 0;
    this.isWaiting = false;
    this.isStreamingResponse = false;
  }

  get first(): RealtimeChatMessage | undefined {
    return this.messages.at(0);
  }

  get firstChunk(): ContentChunk | undefined {
    if (this.first?.type !== "chunk" || this.first?.data.type === "system")
      return;
    return this.first?.data;
  }

  get last(): RealtimeChatMessage | undefined {
    return this.messages.at(-1);
  }

  isStreaming(mtype: MessageType, item_id?: string) {
    if (isMessageType(mtype)) return this.last?.type === mtype;
    if (this.last?.type !== "chunk") return false;
    if (item_id && this.last?.data.item_id !== item_id) return false;
    return this.last?.data.type === mtype;
  }

  update(message: RealtimeChatMessage): void {
    /**
     * Stream context will maintain a contiguous stream of similar message chunks
     * it's mainly used for indicators and to update various UI elements as stream
     * changes.
     */
    if (message.type === "error" || message.type === "turn-end") {
      return this.reset(message.chat_id === this.chatId || !message.chat_id);
    }

    if (message.type === "pong" || message.type === "log") return;
    if (message.chat_id !== this.chatId) {
      return logError("Message chat_id mismatch", null, {
        message,
        chatId: this.chatId,
        expectedChatId: message.chat_id,
        href: window.location.href,
      });
    }

    this.isWaiting = false;
    if (message.type === "chunk" && message.data.type === "system") {
      return this.handleSystemMessage(message.data);
    }

    if (this.first?.type !== message.type) {
      this.messages.length = 0;
    }

    if (this.messages.length === 0) {
      this.messages.push(message);
      return;
    }

    if (message.type !== "chunk" || message.data.type === "system") return;
    const last = this.last!;
    assert(last.type === "chunk", "type check");

    if (
      last.data.type !== message.data.type ||
      last.data.item_id !== message.data.item_id
    ) {
      this.messages.length = 0;
    }

    this.messages.push(message);

    /**
     * Update thinking and tool use content as stream changes
     * Update chat indicator to show sensible messages as stream changes
     */
  }

  private handleSystemMessage(message: ContentChunk) {
    switch (message.message) {
      case "start":
        this.isStreamingResponse = true;
        this.messages.length = 0;
        break;
      case "end":
        this.isStreamingResponse = false;
        this.messages.length = 0;
        break;
    }
  }
}

function isMessageType(mtype: unknown): mtype is RealtimeChatMessage["type"] {
  if (typeof mtype !== "string") return false;
  if (mtype === "error") return true;
  if (mtype === "pong") return true;
  if (mtype === "chunk") return true;
  if (mtype === "item") return true;
  if (mtype === "request") return true;
  if (mtype === "tool-execution-update") return true;
  if (mtype === "request-acknowledge") return true;
  if (mtype === "title-update") return true;
  return false;
}
