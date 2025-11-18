from __future__ import annotations

import time
from typing import TYPE_CHECKING, TypedDict

import frappe

from otto.api.types import RealtimeChunk
from otto.api.utils import publish_activity
from otto.llm.types import TextContentChunk

if TYPE_CHECKING:
	from otto.otto.doctype.otto_chat.otto_chat import OttoChat


class _Directives(TypedDict):
	icl: float
	tool: str | None
	newline: bool


dummy_triggers = {
	"dummy-short": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
	"dummy-medium": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
	"dummy-long": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
}


def is_dummy_query(query: str | None, chat: OttoChat) -> bool:
	if not frappe.conf.developer_mode:
		return False

	if query is None:
		return False

	from otto.assistants.ui_tester import uid

	if chat.assistant != uid:
		return False

	return any(query.startswith(k) for k in dummy_triggers)


def send_dummy_query(query: str, chat: OttoChat) -> None:
	"""
	dummy query format: <trigger>::<directive>
		eg: dummy-medium::icl:50,tool:log,newline

		icl: inter-chunk latency (in ms)
		tool: which tool call to invoke (log, secure_log)
	"""

	parts = query.split("::", 1)
	response = dummy_triggers[parts[0]]
	directives = _parse_directives("" if len(parts) == 1 else parts[1])
	_stream_dummy_response(chat, response, directives)


def _stream_dummy_response(chat: OttoChat, response: str, directive: _Directives):
	from otto.llm.utils import get_agent_item

	assert chat.name is not None, "sanity check"

	new_item = get_agent_item(chat.session_.model)
	start_message = RealtimeChunk(
		id=frappe.generate_hash(length=10),
		data=TextContentChunk(
			type="system",
			message="start",
			content="",
			item_id=new_item["id"],
			session_id=chat.session,
		),
		type="chunk",
		chat_id=chat.name,
	)
	publish_activity(start_message)

	for word in response.split(" "):
		time.sleep(directive["icl"])
		spc = "\n" if directive["newline"] else " "
		message = RealtimeChunk(
			id=frappe.generate_hash(length=10),
			data=TextContentChunk(
				type="text",
				message="content",
				content=word + spc,
				item_id=new_item["id"],
				session_id=chat.session,
			),
			type="chunk",
			chat_id=chat.name,
		)
		publish_activity(message)

	end_message = RealtimeChunk(
		id=frappe.generate_hash(length=10),
		data=TextContentChunk(
			type="system",
			message="end",
			content="",
			item_id=new_item["id"],
			session_id=chat.session,
		),
		type="chunk",
		chat_id=chat.name,
	)
	publish_activity(end_message)


def _parse_directives(directive: str) -> _Directives:
	directives = _Directives(
		icl=0.050,
		tool=None,
		newline=False,
	)

	for part in directive.split(","):
		parts = part.split(":")
		if len(parts) == 1:
			if part == "newline":
				directives["newline"] = True
			continue

		key, value = parts
		if key == "icl":
			directives["icl"] = int(value) / 1000
		elif key == "tool":
			directives["tool"] = value
	return directives
