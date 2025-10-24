import type { SessionItem } from "@/client/generated.types";

export function getUserMessage(query: string): SessionItem {
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
