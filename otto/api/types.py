from typing import Literal, TypedDict

from otto.lib.types import ContentChunk, ReasoningEffort, SessionItem, ToolUseUpdate


class PendingRequest(TypedDict):
	created_at: str
	name: str
	tool_use_id: str


"""
All realtime message items have some associated meta data:
- type: what kind of message it is
- id: unique identifier for the message (so as to avoid duplicates messages)
- chat_id: the chat session id
"""


class Pong(TypedDict):
	message: Literal["pong"]


class RealtimePong(TypedDict):
	id: str
	chat_id: str
	type: Literal["pong"]
	data: Pong


class RealtimeError(TypedDict):
	id: str
	chat_id: str | None
	traceback: str | None
	type: Literal["error"]
	data: str


class RealtimeChunk(TypedDict):
	id: str
	chat_id: str
	type: Literal["chunk"]
	data: ContentChunk


class RealtimeItem(TypedDict):
	id: str
	chat_id: str
	type: Literal["item"]
	data: SessionItem


class RealtimeRequest(TypedDict):
	id: str
	chat_id: str
	type: Literal["request"]
	data: PendingRequest


class RealtimeToolExecutionStart(TypedDict):
	id: str
	chat_id: str
	type: Literal["tool-execution-start"]
	data: int


class RealtimeToolExecutionUpdate(TypedDict):
	id: str
	chat_id: str
	type: Literal["tool-execution-update"]
	data: ToolUseUpdate


class RealtimeRequestAcknowledge(TypedDict):
	id: str
	chat_id: str
	type: Literal["request-acknowledge"]
	data: list[str]  # list of tool use ids that were acknowledged


class RealtimeTurnEnd(TypedDict):
	id: str
	chat_id: str
	type: Literal["turn-end"]
	data: str | None  # reason for why turn end


class RealtimeResumingChat(TypedDict):
	id: str
	chat_id: str
	type: Literal["resuming-chat"]
	data: str | None  # reason for why resuming chat


class RealtimeTitleUpdate(TypedDict):
	id: str
	chat_id: str
	type: Literal["title-update"]
	data: str


class RealtimeLog(TypedDict):
	id: str
	timestamp: str
	type: Literal["log"]
	data: dict | str
	more: dict | None
	traceback: str | None


# @export - used for listening to chat messages
RealtimeChatMessage = (
	RealtimeError
	| RealtimeLog
	| RealtimePong
	| RealtimeChunk
	| RealtimeItem
	| RealtimeRequest
	| RealtimeToolExecutionUpdate
	| RealtimeRequestAcknowledge
	| RealtimeTitleUpdate
	| RealtimeToolExecutionStart
	| RealtimeResumingChat
	| RealtimeTurnEnd
)


class Assistant(TypedDict):
	name: str
	title: str
	llm: str
	reasoning_effort: ReasoningEffort
	supports_user_directives: bool


class AssistantDetails(TypedDict):
	name: str
	title: str
	llm: str
	reasoning_effort: ReasoningEffort | None
	instruction: str
	tools: list[dict]


class AssistantTool(TypedDict):
	tool: str  # Otto Tool name
	title: str
	slug: str
	description: str
	is_valid: bool
	is_enabled: bool
	requires_permission: bool


class ListChatItem(TypedDict):
	creation: str
	modified: str
	name: str
	title: str
	assistant: str


class UserInfo(TypedDict):
	name: str
	email: str


class ChatSettings(TypedDict):
	llm: str | None
	reasoning_effort: Literal["Default"] | ReasoningEffort
	tool_permissions: Literal["Default", "Allow All", "Allow Readonly", "Ask For All", "Ask For Non Readonly"]
	user_directives: str


class Chat(TypedDict):
	name: str
	settings: ChatSettings
	assistant: str
	messages: list[SessionItem]
