from __future__ import annotations

from typing import Any, Literal, NamedTuple, TypedDict, TypeGuard

Provider = Literal["Anthropic", "OpenAI", "Google"]
ModelSize = Literal["Very Small", "Small", "Medium", "Large"]

ID = str
SessionRole = Literal["user", "agent"]
EndReason = Literal["turn_end", "tool_use"]
ReasoningEffort = Literal["Low", "Medium", "High"]


class ThinkingContent(TypedDict):
	type: Literal["thinking"]
	text: str
	signature: str | None  # needed by anthropic


class TextContent(TypedDict):
	type: Literal["text"]
	text: str


class ToolUseContent(TypedDict):
	type: Literal["tool_use"]
	id: str
	name: str
	args: dict
	status: Literal["pending", "success", "error"]
	result: str | None  # set only after tool is invoked

	# Execution Log
	start_time: float
	end_time: float
	stdout: str | None
	stderr: str | None


class ImageContent(TypedDict):
	type: Literal["image"]
	# One of url or data must be set
	url: str | None
	data: str | None  # base64 encoded image data


class FileContent(TypedDict):
	type: Literal["file"]
	name: str
	data: str  # base64 encoded file data, should be a PDF


UserContent = TextContent | ImageContent | FileContent
Content = TextContent | ThinkingContent | ToolUseContent | ImageContent | FileContent


class SessionMeta(TypedDict):
	role: SessionRole
	model: str | None  # If None then item is a human user

	input_tokens: int
	output_tokens: int
	cost: float  # if available in USD

	timestamp: float
	start_time: float
	end_time: float
	end_reason: EndReason | None


class SessionItem(TypedDict):
	id: ID
	next: list[ID]
	selected_next: int  # Used if multiple next items, default 0
	content: list[Content]
	meta: SessionMeta


class Session(TypedDict):
	"""
	Session is modeled as a linked list, where there can be multiple next
	items. This is cause a user might want to handle an interaction from
	any particular point in the session.

	The Session is used to maintain the state of a turn based interaction
	between a user and an agent. Here the user can be a human or an LLM and the
	agent is always an LLM. The identity and nature of the parties involved are
	maintained by the code that makes use of an Session.
	"""

	id: ID
	first: ID
	items: dict[ID, SessionItem]


class ContentChunk(TypedDict):
	"""
	ContentChunk is used to stream content to the user.
	"""

	type: Literal["text", "thinking", "tool_use"]
	content: str
	item_id: str
	session_id: str


class InteractReturn(TypedDict):
	item: SessionItem
	update: Session
	chunks: list[ContentChunk]


class InteractResponse(NamedTuple):
	interaction: SessionItem | None
	reason: str | None


"""
All of the following inputs are converted into list[UserContent]:
- str: input is a single text query
- list[str]: input is list of text queries and urls or paths to images and pdfs
- list[UserContent]: input is list of UserContent

If input is None, it is treated as an empty list. It should be None only if the
session provided has some update such as a tool result.
"""
Query = str | list[str] | list[UserContent] | list[str | UserContent]


class ToolUseUpdate(TypedDict, total=False):
	id: str  # Tool use id
	result: Any
	stdout: str | None
	stderr: str | None
	start_time: float
	end_time: float
	is_error: bool


class ToolSchema(TypedDict):
	name: str
	description: str
	parameters: ToolSchemaParameters


class ToolSchemaParameters(TypedDict):
	type: Literal["object"]
	properties: dict[str, Any]
	required: list[str]
