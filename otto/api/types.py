from typing import Literal, TypedDict

from otto.llm.types import ContentChunk, SessionItem


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


class RealtimeError(TypedDict):
	id: str
	chat_id: str
	type: Literal["error"]
	message: str


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


class RealtimeToolsExecuted(TypedDict):
	id: str
	chat_id: str
	type: Literal["tools-executed"]


# @export - used for listening to chat messages
RealtimeChatMessage = RealtimeChunk | RealtimeItem | RealtimeRequest | RealtimeToolsExecuted | RealtimeError
