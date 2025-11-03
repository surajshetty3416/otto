from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Literal

import frappe

import otto
from otto import lib
from otto.api.types import (
	Assistant,
	PendingRequest,
	RealtimeChatMessage,
	RealtimeChunk,
	RealtimeError,
	RealtimeItem,
	RealtimePong,
	RealtimeRequest,
	RealtimeRequestAcknowledge,
	RealtimeToolExecutionComplete,
	RealtimeToolExecutionUpdate,
)

if TYPE_CHECKING:
	from otto.lib.types import SessionItem
	from otto.llm.types import ModelDetails
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat, ToolConfig
	from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest


logger = otto.logger("otto.api.chat", "ERROR")


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
	"""Continue a chat session with a query."""
	frappe.enqueue(
		_chat,
		timeout=300,
		at_front=True,
		chat_id=chat_id,
		query=query,
	)


@frappe.whitelist()
def resume_chat(chat_id: str) -> None:
	"""Resume a chat session after tool use request is acknowledged."""
	frappe.enqueue(
		_chat,
		timeout=300,
		at_front=True,
		chat_id=chat_id,
		query=None,
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
def list_chats() -> list[dict[str, str]]:
	"""
	List sessions for the sidebar, on clicking load will be called and the user
	can then resume a chat

	List should pull up the sessions along with assistant that was used to create
	the session
	"""
	return frappe.get_all(
		"Otto Chat",
		fields=["name", "title", "assistant"],
		filters={
			"owner": frappe.session.user,
		},
	)


@frappe.whitelist()
def list_models() -> list[ModelDetails]:
	return lib.get_models(get_details=True, include_unavailable=True)


@frappe.whitelist()
def list_assistants() -> list[Assistant]:
	return frappe.get_all(
		"Otto Assistant",
		fields=["name", "title", "llm", "reasoning_effort"],
	)


def _chat(chat_id: str, query: str | None = None) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat = otto.get(OttoChat, chat_id)

	if query is None:
		_execute_tools(chat, chat_id)

	_send_query(chat, chat_id, query)
	_check_pending_requests(chat, chat_id)
	_execute_tools(chat, chat_id)


def _send_query(chat: OttoChat, chat_id: str, query: str | None) -> None:
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
		)
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
	_publish(message)


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
	_publish(message)


@frappe.whitelist()
def delete_chat(chat_id: str) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	for scrapbook_name in frappe.get_all("Otto Scrapbook", filters={"chat": chat_id}, pluck="name"):
		frappe.set_value("Otto Scrapbook", scrapbook_name, "chat", None)

	otto.get(OttoChat, chat_id).delete()


def _check_pending_requests(chat: OttoChat, chat_id: str) -> None:
	pending_requests = chat.get_pending_requests()
	for opr in pending_requests:
		message = RealtimeRequest(
			id=frappe.generate_hash(length=10),
			data=_get_req_from_opr(opr),
			chat_id=chat_id,
			type="request",
		)
		_publish(message)


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


def _execute_tools(chat: OttoChat, chat_id: str) -> None:
	count = 0
	for update in chat.execute_tools():
		message = RealtimeToolExecutionUpdate(
			id=frappe.generate_hash(length=10),
			chat_id=chat_id,
			type="tool-execution-update",
			data=update,
		)
		_publish(message)
		count += 1

	if count == 0:
		return

	message = RealtimeToolExecutionComplete(
		id=frappe.generate_hash(length=10),
		chat_id=chat_id,
		type="tool-execution-complete",
		data=count,
	)
	_publish(message)


def _publish(message: RealtimeChatMessage) -> None:
	frappe.publish_realtime(
		"otto.api.chat",
		user=frappe.session.user,
		message=dict(message),
	)
	logger.debug(
		{
			"message": "published message",
			"user": frappe.session.user,
			"data": dict(message),
		}
	)
