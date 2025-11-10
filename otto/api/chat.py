from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Literal

import frappe

import otto
from otto import lib
from otto.api.types import (
	Assistant,
	AssistantDetails,
	AssistantTool,
	ListChatItem,
	PendingRequest,
	RealtimeChatMessage,
	RealtimeChunk,
	RealtimeError,
	RealtimeItem,
	RealtimePong,
	RealtimeRequest,
	RealtimeRequestAcknowledge,
	RealtimeTitleUpdate,
	RealtimeToolExecutionUpdate,
)

if TYPE_CHECKING:
	from otto.lib.types import SessionItem
	from otto.llm.types import ModelDetails
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat, ToolConfig
	from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest


logger = otto.logger("otto.api.chat", "INFO")


@frappe.whitelist()
def ping(chat_id: str | None = None) -> None:
	"""Used to test if realtime is working"""
	message = RealtimePong(
		id=frappe.generate_hash(length=10),
		data={"message": "pong"},
		chat_id=chat_id or "",
		type="pong",
	)

	frappe.enqueue(
		_publish,
		at_front=True,
		message=message,
	)


@frappe.whitelist()
def new_chat(assistant: str) -> str:
	"""Create a new chat session with an assistant."""
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat = OttoChat.new(assistant)
	assert chat.name is not None, "type check"
	return chat.name


@frappe.whitelist()
def send_query(chat_id: str, query: str) -> None:
	logger.info({"message": "enqueueing-query", "chat_id": chat_id, "query": query, "timestamp": time.time()})

	"""Continue a chat session with a query."""
	frappe.enqueue(
		_chat,
		timeout=300,
		at_front=True,
		queue="short",
		chat_id=chat_id,
		query=query,
		chat=None,
	)


@frappe.whitelist()
def load_chat(chat_id: str) -> list[SessionItem]:
	"""Load the messages of a chat session."""
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat_doc = otto.get(OttoChat, chat_id)
	return chat_doc.session_.get_items()


@frappe.whitelist()
def list_tools(chat_id: str) -> list[ToolConfig]:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	return otto.get(OttoChat, chat_id).tool_configs


@frappe.whitelist()
def list_chats() -> list[ListChatItem]:
	"""
	List sessions for the sidebar, on clicking load will be called and the user
	can then resume a chat

	List should pull up the sessions along with assistant that was used to create
	the session
	"""
	return frappe.get_all(
		"Otto Chat",
		fields=["creation", "modified", "name", "title", "assistant"],
		filters={
			"owner": frappe.session.user,
		},
		order_by="modified desc",
	)


@frappe.whitelist()
def list_models() -> list[ModelDetails]:
	return lib.get_models(get_details=True, include_unavailable=True)


@frappe.whitelist()
def list_assistants() -> list[Assistant]:
	return frappe.get_all(
		"Otto Assistant",
		fields=["name", "title", "llm", "reasoning_effort"],
		order_by="modified desc",
	)


@frappe.whitelist()
def get_preferred_assistants() -> list[str]:
	assistants = frappe.get_all(
		"Otto Chat",
		filters={"owner": frappe.session.user},
		pluck="assistant",
		order_by="modified desc",
		limit=10,
	)

	if not assistants or len(assistants) <= 2:
		return frappe.get_all(
			"Otto Assistant",
			pluck="name",
			limit=3,
			order_by="modified desc",
		)

	count: dict[str, int] = {}
	for assistant in assistants:
		count[assistant] = count.get(assistant, 0) + 1

	asst = [(a, c) for (a, c) in count.items() if a != assistants[0]]
	asst.sort(key=lambda x: x[1], reverse=True)
	sorted = [a for a, _ in asst[:2]]

	# prepend the last used assistant in addition to most used
	return [assistants[0], *sorted]


@frappe.whitelist()
def get_assistant_details(name: str) -> AssistantDetails:
	from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant

	assistant = otto.get(OttoAssistant, name)
	assert assistant.name is not None, "sanity check"
	tools = []
	tool_names = set([tool.tool for tool in assistant.tools])
	tool_list = frappe.get_all(
		"Otto Tool",
		filters={"name": ["in", tool_names]},
		fields=["name", "title", "description", "is_valid", "slug", "description"],
	)
	tool_map = {tool.name: tool for tool in tool_list}

	for tool in assistant.tools:
		tool_data = tool_map.get(tool.tool)
		if not tool_data:
			continue

		tools.append(
			AssistantTool(
				tool=tool.tool,
				title=tool_data.title or tool_data.slug or "",
				slug=tool.slug or tool_data.slug,
				description=tool_data.description or "",
				is_valid=bool(tool_data.is_valid),
				is_enabled=bool(tool.is_enabled),
				requires_permission=bool(tool.requires_permission),
			)
		)

	return AssistantDetails(
		name=assistant.name,
		title=assistant.title,
		llm=assistant.llm,
		reasoning_effort=assistant.reasoning_effort if assistant.reasoning_effort != "None" else None,
		instruction=assistant.instruction,
		tools=tools,
	)


def _chat(chat_id: str, query: str | None = None, chat: OttoChat | None = None) -> None:
	logger.info({"message": "processing-query", "chat_id": chat_id, "query": query, "timestamp": time.time()})
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	if chat is None:
		chat = otto.get(OttoChat, chat_id)

	_send_query(chat_id, chat, query)
	_check_pending_requests(chat_id, chat)
	_execute_tools(chat_id, chat)

	if (not chat.title or chat.title.startswith("New Chat")) and len(chat.session_.get_items()) >= 3:
		frappe.enqueue(
			_autoset_title,
			chat_id=chat_id,
		)


def _autoset_title(chat_id: str) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat = otto.get(OttoChat, chat_id)
	if not chat.autoset_title() or not chat.title:
		return

	message = RealtimeTitleUpdate(
		id=frappe.generate_hash(length=10),
		chat_id=chat_id,
		type="title-update",
		data=chat.title,
	)
	_publish(message)


def _send_query(chat_id: str, chat: OttoChat, query: str | None) -> None:
	response, reason = chat.chat(query)
	if reason:
		message = RealtimeError(
			id=frappe.generate_hash(length=10),
			data=reason,
			chat_id=chat_id,
			type="error",
		)
		_publish(message)
		return

	assert response is not None, "sanity check"
	for chunk in response:
		message = RealtimeChunk(
			id=frappe.generate_hash(length=10),
			data=chunk,
			type="chunk",
			chat_id=chat_id,
		)
		_publish(message)

	assert response.item is not None, "sanity check"
	_publish(
		RealtimeItem(
			id=frappe.generate_hash(length=10),
			data=response.item,
			chat_id=chat_id,
			type="item",
		),
		after_commit=True,
	)


@frappe.whitelist()
def get_pending_requests(chat_id: str) -> list[PendingRequest]:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat = otto.get(OttoChat, chat_id)
	return [_get_req_from_opr(opr) for opr in chat.get_pending_requests()]


@frappe.whitelist()
def acknowledge_request(
	request_id: str,
	status: Literal["Granted", "Denied"],
) -> None:
	from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest

	opr = otto.get(OttoPermissionRequest, request_id)
	old_status = opr.status

	opr.acknowledge(status=status)
	if not opr.chat or old_status != "Pending":  # prevent double publish
		return

	message = RealtimeRequestAcknowledge(
		id=frappe.generate_hash(length=10),
		chat_id=opr.chat,
		type="request-acknowledge",
		data=[opr.tool_use_id],
	)
	_publish(message, after_commit=True)
	_enqueue_execution(opr.chat)


@frappe.whitelist()
def acknowledge_all_requests(
	chat_id: str,
	status: Literal["Granted", "Denied"],
) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	tool_use_ids = []

	chat = otto.get(OttoChat, chat_id)
	for opr in chat.get_pending_requests():
		tool_use_ids.append(opr.tool_use_id)
		opr.acknowledge(status=status)

	message = RealtimeRequestAcknowledge(
		id=frappe.generate_hash(length=10),
		chat_id=chat_id,
		type="request-acknowledge",
		data=tool_use_ids,
	)
	_publish(message, after_commit=True)
	_enqueue_execution(chat_id)


def _enqueue_execution(chat_id: str) -> None:
	frappe.enqueue(
		_execute_tools,
		timeout=300,
		at_front=True,
		queue="short",
		chat_id=chat_id,
		chat=None,
	)


@frappe.whitelist()
def delete_chat(chat_id: str) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	for scrapbook_name in frappe.get_all("Otto Scrapbook", filters={"chat": chat_id}, pluck="name"):
		frappe.set_value("Otto Scrapbook", scrapbook_name, "chat", None)

	otto.get(OttoChat, chat_id).delete()


def _check_pending_requests(chat_id: str, chat: OttoChat) -> list[OttoPermissionRequest]:
	pending_requests = chat.get_pending_requests()
	for opr in pending_requests:
		message = RealtimeRequest(
			id=frappe.generate_hash(length=10),
			data=_get_req_from_opr(opr),
			chat_id=chat_id,
			type="request",
		)
		_publish(message, after_commit=True)
	return pending_requests


def _get_req_from_opr(opr: OttoPermissionRequest) -> PendingRequest:
	assert opr.name is not None
	created_at = opr.creation
	if isinstance(created_at, datetime.datetime):
		created_at = created_at.isoformat()
	return PendingRequest(
		created_at=created_at,
		name=opr.name,
		tool_use_id=opr.tool_use_id,
	)


def _execute_tools(
	chat_id: str,
	chat: OttoChat | None,
) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	if chat is None:
		chat = otto.get(OttoChat, chat_id)

	for update in chat.execute_tools():
		message = RealtimeToolExecutionUpdate(
			id=frappe.generate_hash(length=10),
			chat_id=chat_id,
			type="tool-execution-update",
			data=update,
		)
		_publish(message)

	if not chat.can_resume():
		return

	_chat(
		chat_id=chat_id,
		chat=chat,
		query=None,
	)


def _publish(message: RealtimeChatMessage, after_commit: bool = False) -> None:
	frappe.publish_realtime(
		"otto.api.chat",
		user=frappe.session.user,
		message=dict(message),
		after_commit=after_commit,
	)
	logger.debug(
		{
			"message": "published message",
			"user": frappe.session.user,
			"data": dict(message),
		}
	)
