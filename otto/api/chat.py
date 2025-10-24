import datetime

import frappe

import otto
from otto.api.types import (
	PendingRequest,
	RealtimeChatMessage,
	RealtimeChunk,
	RealtimeError,
	RealtimeItem,
	RealtimeRequest,
	RealtimeToolsExecuted,
)
from otto.llm.types import SessionItem


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
def list_chats():
	"""
	List sessions for the sidebar, on clicking load will be called and the user
	can then resume a chat

	List should pull up the sessions along with assistant that was used to create
	the session
	"""
	pass


@frappe.whitelist()
def list_assistants():
	"""
	List assistants that the user can use to chat with.

	Once an assistant is selected the user cannot change it for a
	chat session. The user can configure the underlying session by
	selecting the LLM and available tools but not the assistant.
	"""
	pass


def _chat(chat_id: str, query: str | None = None) -> None:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat

	chat = otto.get(OttoChat, chat_id)
	response, reason = chat.chat(query)
	if reason:
		message = RealtimeError(
			id=frappe.generate_hash(length=10),
			message=reason,
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

	pending_requests = chat.get_pending_requests()
	for opr in pending_requests:
		assert opr.name is not None
		created_at = opr.creation
		if isinstance(created_at, datetime.datetime):
			created_at = created_at.isoformat()

		request = PendingRequest(
			created_at=created_at,
			name=opr.name,
			tool_use_id=opr.tool_use_id,
		)
		message = RealtimeRequest(
			id=frappe.generate_hash(length=10),
			data=request,
			chat_id=chat_id,
			type="request",
		)
		_publish(message)

	if chat.execute_tools():
		# TODO:
		# execute tools in a generator, publish updates as tools are being
		# executed and then publish the final result "ask to resume"
		message = RealtimeToolsExecuted(
			id=frappe.generate_hash(length=10),
			chat_id=chat_id,
			type="tools-executed",
		)
		_publish(message)


def _publish(message: RealtimeChatMessage) -> None:
	frappe.publish_realtime(
		"otto.api.chat",
		user=frappe.session.user,
		message=dict(message),
	)
