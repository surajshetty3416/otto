import type { AssertTrue, CheckIsRawAPI } from "./types";

export interface BaseDoc<T extends string> {
  name: string | number;
  owner?: string;
  creation?: string;
  modified?: string;
  modified_by?: string;
  docstatus?: number;
  idx?: number;
  doctype?: T;
}

// <DocType Types for Otto>
// Auto-generated using `bench generate-types`. Do not edit.

export interface OttoScrapbook extends BaseDoc<"Otto Scrapbook"> {
  tool?: string;
  task?: string;
  content?: string;
  session?: string;
  chat?: string;
}

export interface OttoAssistant extends BaseDoc<"Otto Assistant"> {
  title: string;
  llm: string;
  get_context?: string;
  instruction: string;
  reasoning_effort?: "None" | "Low" | "Medium" | "High";
  tools?: OttoAssistantToolCT[];
  is_app_defined?: number | boolean;
  get_context_import_path?: string;
  supports_user_directives?: number | boolean;
}

export interface OttoToolGroup extends BaseDoc<"Otto Tool Group"> {
  description?: string;
}

export interface OttoAssistantToolCT extends BaseDoc<"Otto Assistant Tool CT"> {
  slug?: string;
  is_enabled?: number | boolean;
  requires_permission?: number | boolean;
  tool: string;
}

export interface OttoChatToolCT extends BaseDoc<"Otto Chat Tool CT"> {
  slug?: string;
  is_enabled?: number | boolean;
  requires_permission?: number | boolean;
  tool: string;
}

export interface OttoPermissionRequest
  extends BaseDoc<"Otto Permission Request"> {
  tool_use_id: string;
  tool_status?: string;
  status: "Pending" | "Granted" | "Denied";
  session: string;
  tool_name?: string;
  tool_use_result?: string;
  tool_use_args?: string;
  execution?: string;
  task?: string;
  target_doctype?: string;
  target?: string;
  tool_slug?: string;
  descriptions?: string;
  args_updated?: number | boolean;
  denied_reason?: string;
  is_autoset?: number | boolean;
}

export interface OttoToolArgCT extends BaseDoc<"Otto Tool Arg CT"> {
  type: string;
  description?: string;
  arg_name: string;
  is_required?: number | boolean;
}

export interface OttoChat extends BaseDoc<"Otto Chat"> {
  title?: string;
  assistant: string;
  session: string;
  tools?: OttoChatToolCT[];
  llm?: string;
  reasoning_effort?: "None" | "Low" | "Medium" | "High";
  user_directives?: string;
  tool_permissions?:
    | "Default"
    | "Allow All"
    | "Allow Readonly"
    | "Ask For All"
    | "Ask For Non Readonly";
}

export interface OttoTaskToolCT extends BaseDoc<"Otto Task Tool CT"> {
  tool: string;
  is_enabled?: number | boolean;
  env?: string;
  slug?: string;
}

export interface OttoFeedback extends BaseDoc<"Otto Feedback"> {
  comment?: string;
  value?: number;
  session?: string;
}

export interface OttoTool extends BaseDoc<"Otto Tool"> {
  code?: string;
  description?: string;
  args?: OttoToolArgCT[];
  slug: string;
  is_valid?: number | boolean;
  reason?: string;
  mock_tool?: number | boolean;
  mock_return_value?: string;
  requires_permission?: number | boolean;
  title?: string;
  use_explanation?: number | boolean;
  is_external?: number | boolean;
  tool_import_path?: string;
  is_app_defined?: number | boolean;
  is_readonly?: number | boolean;
  is_destructive?: number | boolean;
  is_idempotent?: number | boolean;
  is_open_world?: number | boolean;
}

export interface OttoSessionItemCT extends BaseDoc<"Otto Session Item CT"> {
  uid: string;
  next?: string;
  selected?: number;
  role: string;
  input_tokens?: number;
  start_time?: string;
  end_reason?: string;
  cost?: number;
  model?: string;
  output_tokens?: number;
  end_time?: string;
  timestamp: string;
  content: string;
  is_selected?: number | boolean;
  inter_chunk_latency?: number;
  time_to_first_chunk?: number;
}

export interface OttoSession extends BaseDoc<"Otto Session"> {
  llm?: string;
  instruction?: string;
  reasoning_effort?: "None" | "Low" | "Medium" | "High";
  items?: OttoSessionItemCT[];
  uid?: string;
  first?: string;
  is_active?: number | boolean;
  reason?: string;
  tools?: OttoSessionToolCT[];
  reference_doctype?: string;
  reference_name?: string;
}

export interface OttoSessionToolCT extends BaseDoc<"Otto Session Tool CT"> {
  slug: string;
  properties?: string;
  required?: string;
  description: string;
}

export interface OttoExecution extends BaseDoc<"Otto Execution"> {
  event?: string;
  task: string;
  status: "Pending" | "Waiting" | "Running" | "Success" | "Failure";
  reason?: string;
  target?: string;
  target_doctype?: string;
  session: string;
}

export interface OttoLLM extends BaseDoc<"Otto LLM"> {
  provider: "Anthropic" | "OpenAI" | "Google";
  title: string;
  enabled?: number | boolean;
  is_reasoning?: number | boolean;
  size?: "Very Small" | "Small" | "Medium" | "Large";
  supports_vision?: number | boolean;
}

export interface OttoSettings extends BaseDoc<"Otto Settings"> {
  is_enabled?: number | boolean;
  global_env?: string;
  task_execution_timeout?: number;
  max_llm_calls?: number;
}

export interface OttoTask extends BaseDoc<"Otto Task"> {
  instruction?: string;
  event:
    | "On Create"
    | "On Update"
    | "On Delete"
    | "On Submit"
    | "On Cancel"
    | "Manual";
  title?: string;
  is_enabled?: number | boolean;
  get_context?: string;
  tools?: OttoTaskToolCT[];
  target_doctype?: string;
  llm?: string;
  condition?: string;
  reasoning_effort?: "None" | "Low" | "Medium" | "High";
  no_target?: number | boolean;
}

export interface OttoDocTypes {
  "Otto Scrapbook": OttoScrapbook;
  "Otto Assistant": OttoAssistant;
  "Otto Tool Group": OttoToolGroup;
  "Otto Assistant Tool CT": OttoAssistantToolCT;
  "Otto Chat Tool CT": OttoChatToolCT;
  "Otto Permission Request": OttoPermissionRequest;
  "Otto Tool Arg CT": OttoToolArgCT;
  "Otto Chat": OttoChat;
  "Otto Task Tool CT": OttoTaskToolCT;
  "Otto Feedback": OttoFeedback;
  "Otto Tool": OttoTool;
  "Otto Session Item CT": OttoSessionItemCT;
  "Otto Session": OttoSession;
  "Otto Session Tool CT": OttoSessionToolCT;
  "Otto Execution": OttoExecution;
  "Otto LLM": OttoLLM;
  "Otto Settings": OttoSettings;
  "Otto Task": OttoTask;
}
// </DocType Types for Otto>

// <API Types for Otto>
// Auto-generated using `bench generate-types`. Do not edit.

// otto/otto/llm/types.py
export interface SessionItem {
  id: ID;
  next: ID[];
  selected_next: number;
  content: Content[];
  meta: Meta;
}

// otto/otto/api/types.py
export interface AssistantDetails {
  name: string;
  title: string;
  llm: string;
  reasoning_effort: ReasoningEffort | null;
  instruction: string;
  tools: Record<string, unknown>[];
}

// otto/otto/otto/doctype/otto_chat/otto_chat.py
export interface ToolConfig {
  title: string;
  slug: string;
  tool: string;
  is_external: boolean;
  requires_permission: boolean;
  is_valid: boolean;
  reason: string | null;
  use_explanation: boolean;
  is_readonly: boolean;
}

// otto/otto/llm/types.py
export type Content =
  | TextContent
  | ThinkingContent
  | ToolUseContent
  | ImageContent
  | FileContent;

// otto/otto/llm/types.py
export interface ImageContent {
  type: "image";
  url: string | null;
  data: string | null;
}

// otto/otto/llm/types.py
export interface FileContent {
  type: "file";
  name: string;
  data: string;
}

// otto/otto/api/types.py
export interface Assistant {
  name: string;
  title: string;
  llm: string;
  reasoning_effort: ReasoningEffort;
}

// otto/otto/llm/types.py
export type ReasoningEffort = "Low" | "Medium" | "High" | "None";

// otto/otto/llm/types.py
export interface ModelDetails {
  name: string;
  provider: Provider;
  size: ModelSize;
  is_reasoning: boolean;
  supports_vision: boolean;
  title: string;
  is_enabled: boolean;
  is_api_key_set: boolean;
}

// otto/otto/api/types.py
export interface ListChatItem {
  creation: string;
  modified: string;
  name: string;
  title: string;
  assistant: string;
}

// otto/otto/llm/types.py
export interface TextContent {
  type: "text";
  text: string;
}

// otto/otto/api/types.py
export interface ChatSettings {
  llm: string | null;
  reasoning_effort: ReasoningEffort | null;
  tool_permissions:
    | "Default"
    | "Allow All"
    | "Allow Readonly"
    | "Ask For All"
    | "Ask For Non Readonly"
    | null;
  user_directives: string | null;
}

// otto/otto/api/types.py
export interface UserInfo {
  name: string;
  email: string;
}

// otto/otto/llm/types.py
export type Provider = "Anthropic" | "OpenAI" | "Google";

// otto/otto/llm/types.py
export type ID = string;

// otto/otto/llm/types.py
export interface Meta {
  role: SessionRole;
  model: string | null;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  timestamp: number;
  start_time: number;
  end_time: number;
  end_reason: EndReason | null;
  time_to_first_chunk: number;
  inter_chunk_latency: number;
}

// otto/otto/llm/types.py
export interface ThinkingContent {
  type: "thinking";
  text: string;
  signature: string | null;
}

// otto/otto/llm/types.py
export interface ToolUseContent {
  type: "tool_use";
  id: string;
  name: string;
  status: "pending" | "success" | "error";
  result: string | null;
  _args: string | null;
  args: Record<string, unknown>;
  override: Record<string, unknown> | null;
  start_time: number;
  end_time: number;
  stdout: string | null;
  stderr: string | null;
}

// otto/otto/llm/types.py
export type SessionRole = "user" | "agent";

// otto/otto/llm/types.py
export type ModelSize = "Very Small" | "Small" | "Medium" | "Large";

// otto/otto/llm/types.py
export type EndReason = "turn_end" | "tool_use";

export interface API {
  session_view: {
    get_session_view(args: { name: string }): unknown;
    get_adjacent_session(args: {
      name: string;
      next: string | boolean;
    }): unknown;
    get_recent_sessions(args: {
      limit?: number;
      page?: number;
    }): Record<string, unknown>[];
  };
  ping(): "pong";
  echo(args: { message: string }): string;
  get_user(): string;
  get_user_info(): UserInfo | null;
  log_feedback(): unknown;
  chat: {
    ping(args: { chat_id?: string | null }): null;
    new_chat(args: {
      assistant: string;
      settings?: ChatSettings | null;
    }): string;
    send_query(args: { chat_id: string; query: string }): null;
    load_messages(args: { chat_id: string }): SessionItem[];
    load_settings(args: { chat_id: string }): ChatSettings;
    save_settings(args: {
      chat_id: string;
      settings?: ChatSettings | null;
    }): null;
    list_tools(args: { chat_id: string }): ToolConfig[];
    list_chats(): ListChatItem[];
    list_models(): ModelDetails[];
    list_assistants(): Assistant[];
    get_preferred_assistants(): string[];
    get_assistant_details(args: { name: string }): AssistantDetails;
    get_pending_requests(args: { chat_id: string }): PendingRequest[];
    acknowledge_request(args: {
      request_id: string;
      status: "Granted" | "Denied";
    }): null;
    acknowledge_all_requests(args: {
      chat_id: string;
      status: "Granted" | "Denied";
    }): null;
    delete_chat(args: { chat_id: string }): null;
  };
  permissions: {
    add_viewed(args: { name: string }): unknown;
    acknowledge(args: {
      name: string;
      type: "grant" | "deny";
      override_args?: Record<string, unknown> | null;
      denied_reason?: string | null;
    }): null;
    get_pending_requests(args: {
      task?: string | null;
      execution?: string | null;
      target?: string | null;
      tool_slug?: string | null;
      tool_name?: string | null;
      target_doctype?: string | null;
      session?: string | null;
      tool_use_id?: string | null;
    }): Record<string, unknown>[];
  };
  client_test: {
    add_numbers(args: { a: number; b: number }): number;
    greet(args: { name: string; greeting?: string }): string;
    get_user_info(args: {
      user_id: string;
      include_details?: boolean;
    }): Record<string, unknown>;
    process_items(args: { items: unknown[] }): Record<string, unknown>;
    validate_credentials(args: {
      username: string;
      password: string;
    }): Record<string, unknown>;
    calculate(args: {
      operation: string;
      x: number;
      y: number;
    }): Record<string, unknown>;
    get_list(args: { limit?: number; offset?: number }): unknown[];
    create_record(args: {
      name: string;
      data: Record<string, unknown>;
    }): Record<string, unknown>;
    test_error(args: { should_fail?: boolean }): Record<string, unknown>;
    get_random(): number;
    throw(args: { message: string; use_frappe?: boolean }): unknown;
  };
}
// </API Types for Otto>

// @ts-ignore - assert that generated API conforms to the expected structure
type _ = AssertTrue<CheckIsRawAPI<API>>;

// <Exported Types for Otto>
// Auto-generated using `bench generate-types`. Do not edit.

// otto/otto/api/types.py
export interface RealtimeToolExecutionUpdate {
  id: string;
  chat_id: string;
  type: "tool-execution-update";
  data: ToolUseUpdate;
}

// otto/otto/api/types.py
export interface RealtimeChunk {
  id: string;
  chat_id: string;
  type: "chunk";
  data: ContentChunk;
}

// otto/otto/api/types.py
export interface RealtimeItem {
  id: string;
  chat_id: string;
  type: "item";
  data: SessionItem;
}

// otto/otto/llm/types.py
export type ContentChunk = TextContentChunk | ToolUseContentChunk;

// otto/otto/api/types.py
export interface RealtimeRequest {
  id: string;
  chat_id: string;
  type: "request";
  data: PendingRequest;
}

// otto/otto/api/types.py
export interface RealtimeRequestAcknowledge {
  id: string;
  chat_id: string;
  type: "request-acknowledge";
  data: string[];
}

// otto/otto/api/types.py
export interface RealtimeError {
  id: string;
  chat_id: string;
  type: "error";
  data: string;
}

// otto/otto/api/types.py
export interface RealtimeTitleUpdate {
  id: string;
  chat_id: string;
  type: "title-update";
  data: string;
}

// otto/otto/llm/types.py
export interface TextContentChunk {
  type: "text" | "thinking" | "system";
  message: "start" | "end" | "error" | "content";
  content: string;
  item_id: string;
  session_id: string;
}

// otto/otto/api/types.py
export interface RealtimePong {
  id: string;
  chat_id: string;
  type: "pong";
  data: Pong;
}

// otto/otto/api/types.py
export interface PendingRequest {
  created_at: string;
  name: string;
  tool_use_id: string;
}

// otto/otto/llm/types.py
export interface ToolUseContentChunk {
  type: "tool_use";
  message: "start" | "end" | "error" | "content";
  content: ToolUseDelta;
  item_id: string;
  session_id: string;
}

// otto/otto/llm/types.py
export interface ToolUseUpdate {
  id: string;
  result: unknown;
  stdout: string | null;
  stderr: string | null;
  start_time: number;
  end_time: number;
  is_error: boolean;
}

// otto/otto/api/types.py
export interface Pong {
  message: "pong";
}

// otto/otto/llm/types.py
export interface ToolUseDelta {
  id: string | null;
  name: string | null;
  args: string | null;
}

// otto/otto/api/types.py
export type RealtimeChatMessage =
  | RealtimeError
  | RealtimePong
  | RealtimeChunk
  | RealtimeItem
  | RealtimeRequest
  | RealtimeToolExecutionUpdate
  | RealtimeRequestAcknowledge
  | RealtimeTitleUpdate;
// </Exported Types for Otto>
