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
  title?: string;
  llm?: string;
  get_context?: string;
  instruction?: string;
  reasoning_effort?: "None" | "Low" | "Medium" | "High";
  tools?: OttoAssistantToolCT[];
}

export interface OttoToolGroup extends BaseDoc<"Otto Tool Group"> {
  description?: string;
}

export interface OttoAssistantToolCT extends BaseDoc<"Otto Assistant Tool CT"> {
  slug: string;
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
  is_enabled?: number | boolean;
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
  ping(): unknown;
  echo(args: { message: string }): string;
  throw(args: { message: string; use_frappe?: boolean }): unknown;
  get_user(): Record<string, string>;
  log_feedback(): unknown;
  chat: {
    test(): unknown;
    chat(args: { query: string }): unknown;
    load(args: { session: string }): unknown;
    list_chats(): unknown;
    list_assistants(): unknown;
  };
  permissions: {
    add_viewed(args: { name: string }): unknown;
    acknowledge(args: {
      name: string;
      type: "grant" | "deny";
      override_args?: Record<string, unknown> | null;
      denied_reason?: string | null;
    }): unknown;
    get_pending_requests(args: {
      task?: string | null;
      execution?: string | null;
      target?: string | null;
      tool_slug?: string | null;
      tool_name?: string | null;
      target_doctype?: string | null;
      session?: string | null;
      tool_use_id?: string | null;
    }): unknown;
  };
}
// </API Types for Otto>

// Assert that generated API conforms to the expected structure
type _ = AssertTrue<CheckIsRawAPI<API>>;
