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
	chat_id: str
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


class RealtimeToolExecutionUpdate(TypedDict):
	id: str
	chat_id: str
	type: Literal["tool-execution-update"]
	data: ToolUseUpdate


class RealtimeToolExecutionComplete(TypedDict):
	id: str
	chat_id: str
	type: Literal["tool-execution-complete"]
	data: int


class RealtimeRequestAcknowledge(TypedDict):
	id: str
	chat_id: str
	type: Literal["request-acknowledge"]
	data: list[str]  # list of tool use ids that were acknowledged


# @export - used for listening to chat messages
RealtimeChatMessage = (
	RealtimeError
	| RealtimePong
	| RealtimeChunk
	| RealtimeItem
	| RealtimeRequest
	| RealtimeToolExecutionUpdate
	| RealtimeToolExecutionComplete
	| RealtimeRequestAcknowledge
)


class Assistant(TypedDict):
	name: str
	title: str
	llm: str
	reasoning_effort: ReasoningEffort
