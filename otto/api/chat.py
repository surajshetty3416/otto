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
	Chat,
	ChatSettings,
	ListChatItem,
	PendingRequest,
	RealtimeChunk,
	RealtimeError,
	RealtimeItem,
	RealtimePong,
	RealtimeRequest,
	RealtimeRequestAcknowledge,
	RealtimeResumingChat,
	RealtimeTitleUpdate,
	RealtimeToolExecutionStart,
	RealtimeToolExecutionUpdate,
	RealtimeTurnEnd,
)
from otto.api.utils import inform_on_error, publish_activity

if TYPE_CHECKING:
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
		publish_activity,
		at_front=True,
		message=message,
	)


@frappe.whitelist()
def new_chat(assistant: str, settings: ChatSettings | None = None) -> str:
	"""Create a new chat session with an assistant."""
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	settings = settings or ChatSettings(
		llm=None,
		reasoning_effort="Default",
		tool_permissions="Default",
		user_directives="",
	)

	chat = OttoChat.new(
		assistant,
		llm=settings["llm"],
		reasoning_effort=settings["reasoning_effort"],
		tool_permissions=settings["tool_permissions"],
		user_directives=settings["user_directives"],
	)

	assert chat.name is not None, "type check"
	return chat.name


@frappe.whitelist()
def send_query(chat_id: str, query: str) -> None:
	log_id = (frappe.generate_hash(length=10),)
	logger.info(
		{
			"message": "enqueueing-query",
			"chat_id": chat_id,
			"query": query,
			"log_id": log_id,
			"timestamp": time.time(),
		}
	)

	"""Continue a chat session with a query."""
	frappe.enqueue(
		_chat,
		timeout=300,
		at_front=True,
		queue="short",
		chat_id=chat_id,
		query=query,
		chat=None,
		log_id=log_id,
	)


@frappe.whitelist()
def load_chat(chat_id: str) -> Chat:
	"""Load the chat messages."""
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat_doc = otto.get(OttoChat, chat_id)
	assert chat_doc.name is not None, "type check"
	return Chat(
		name=chat_doc.name,
		settings=ChatSettings(
			llm=chat_doc.llm,
			reasoning_effort=chat_doc.reasoning_effort,
			tool_permissions=chat_doc.tool_permissions,
			user_directives=chat_doc.user_directives or "",
		),
		assistant=chat_doc.assistant,
		messages=chat_doc.session_.get_items(),
	)


@frappe.whitelist()
def load_settings(chat_id: str) -> ChatSettings:
	vals = frappe.db.get_value(
		"Otto Chat",
		chat_id,
		fieldname=["llm", "reasoning_effort", "tool_permissions", "user_directives"],
		as_dict=True,
	)
	assert isinstance(vals, dict), "type check"
	return ChatSettings(
		llm=vals["llm"],
		reasoning_effort=vals["reasoning_effort"],
		tool_permissions=vals["tool_permissions"],
		user_directives=vals["user_directives"],
	)


@frappe.whitelist()
def save_settings(chat_id: str, settings: ChatSettings) -> ChatSettings:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat_doc = otto.get(OttoChat, chat_id)

	chat_doc.update_settings(
		llm=settings["llm"],
		reasoning_effort=settings["reasoning_effort"],
		tool_permissions=settings["tool_permissions"],
		user_directives=settings["user_directives"],
	)
	chat_doc.save()
	return ChatSettings(
		llm=chat_doc.llm,
		reasoning_effort=chat_doc.reasoning_effort,
		tool_permissions=chat_doc.tool_permissions,
		user_directives=chat_doc.user_directives or "",
	)


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
	_assistants = frappe.get_all(
		"Otto Assistant",
		fields=["name", "title", "llm", "reasoning_effort", "supports_user_directives"],
		order_by="modified desc",
	)
	assistants: list[Assistant] = []
	for ast in _assistants:
		assistants.append(
			Assistant(
				name=ast.name,
				title=ast.title,
				llm=ast.llm,
				reasoning_effort=ast.reasoning_effort,
				supports_user_directives=bool(ast.supports_user_directives),
			)
		)
	return assistants


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


@inform_on_error
def _chat(
	chat_id: str,
	query: str | None = None,
	chat: OttoChat | None = None,
	log_id: str | None = None,
) -> None:
	logger.info(
		{
			"message": "processing-query",
			"chat_id": chat_id,
			"query": query,
			"log_id": log_id,  # Used to track queue wait time
			"timestamp": time.time(),
		}
	)
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	if chat is None:
		chat = otto.get(OttoChat, chat_id)

	_send_query(chat_id, chat, query)
	_check_pending_requests(chat_id, chat)
	_execute_tools(chat_id, chat, check_pending_requests=False)

	if (not chat.title or chat.title.startswith("New Chat")) and len(chat.session_.get_items()) >= 3:
		frappe.enqueue(
			_autoset_title,
			chat_id=chat_id,
		)


@inform_on_error
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
	publish_activity(message)


def _send_query(chat_id: str, chat: OttoChat, query: str | None) -> None:
	from otto.api.dummy import is_dummy_query, send_dummy_query

	if is_dummy_query(query, chat):
		assert query is not None, "type check"
		send_dummy_query(query, chat)
		return

	response, reason = chat.chat(query)
	if reason:
		message = RealtimeError(
			id=frappe.generate_hash(length=10),
			data=reason,
			traceback=None,
			chat_id=chat_id,
			type="error",
		)
		publish_activity(message)
		return

	assert response is not None, "sanity check"
	for chunk in response:
		message = RealtimeChunk(
			id=frappe.generate_hash(length=10),
			data=chunk,
			type="chunk",
			chat_id=chat_id,
		)
		publish_activity(message)

	assert response.item is not None, "sanity check"
	frappe.db.commit()
	publish_activity(
		RealtimeItem(
			id=frappe.generate_hash(length=10),
			data=response.item,
			chat_id=chat_id,
			type="item",
		),
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
	publish_activity(message, after_commit=True)
	_enqueue_tool_execution(opr.chat)


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
	publish_activity(message, after_commit=True)
	_enqueue_tool_execution(chat_id)


def _enqueue_tool_execution(chat_id: str) -> None:
	frappe.enqueue(
		_execute_tools,
		timeout=300,
		at_front=True,
		queue="short",
		chat_id=chat_id,
		chat=None,
		check_pending_requests=True,
	)


@frappe.whitelist()
def delete_chat(chat_id: str) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	for scrapbook_name in frappe.get_all("Otto Scrapbook", filters={"chat": chat_id}, pluck="name"):
		frappe.set_value("Otto Scrapbook", scrapbook_name, "chat", None)

	otto.get(OttoChat, chat_id).delete()


def _check_pending_requests(chat_id: str, chat: OttoChat) -> list[OttoPermissionRequest]:
	pending_requests = chat.get_pending_requests()
	otto.log_realtime(f"Found {len(pending_requests)} pending requests", traceback=True)
	if len(pending_requests):
		frappe.db.commit()

	for opr in pending_requests:
		message = RealtimeRequest(
			id=frappe.generate_hash(length=10),
			data=_get_req_from_opr(opr),
			chat_id=chat_id,
			type="request",
		)
		publish_activity(message)
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


@inform_on_error
def _execute_tools(
	chat_id: str,
	chat: OttoChat | None,
	check_pending_requests: bool = False,
) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	otto.log_realtime(f"_execute_tools [{chat_id}]", traceback=True)

	if chat is None:
		chat = otto.get(OttoChat, chat_id)

	if check_pending_requests:
		_check_pending_requests(chat_id, chat)

	for update in chat.execute_tools():
		# This is admittedly a bit weird. The first yield is a list of pending
		# permitted tools, used to indicate the start of the tool execution
		# loop.
		if isinstance(update, list) and len(update) > 0:
			message = RealtimeToolExecutionStart(
				id=frappe.generate_hash(length=10),
				chat_id=chat_id,
				type="tool-execution-start",
				data=len(update),
			)
			publish_activity(message)
			continue

		if isinstance(update, list):
			continue

		message = RealtimeToolExecutionUpdate(
			id=frappe.generate_hash(length=10),
			chat_id=chat_id,
			type="tool-execution-update",
			data=update,
		)
		publish_activity(message)

	can_resume, reason = chat.can_resume()
	otto.log_realtime(f"{'Resuming' if can_resume else 'Turn ended'} [{chat_id}]: {reason}", traceback=True)
	if not can_resume:
		message = RealtimeTurnEnd(
			id=frappe.generate_hash(length=10),
			chat_id=chat_id,
			type="turn-end",
			data=reason,
		)
		publish_activity(message)
		return

	_chat(
		chat_id=chat_id,
		chat=chat,
		query=None,
	)
	message = RealtimeResumingChat(
		id=frappe.generate_hash(length=10),
		chat_id=chat_id,
		type="resuming-chat",
		data=reason,
	)
	publish_activity(message)
