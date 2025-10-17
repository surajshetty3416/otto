from __future__ import annotations

import datetime
import json
import os
import time
import uuid
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, TypeGuard

import frappe

from otto import utils
from otto.llm.types import SessionStats, SessionToolUseStats

if TYPE_CHECKING:
	from otto.llm.types import Provider, Query, ReasoningEffort, Session, ToolUseContent

MAX_RETRIES = 6
DEFAULT_INSTRUCTION = "You are a helpful assistant."
DEFAULT_MODEL = "openai/gpt-4.1-nano"
DEFAULT_REASONING_BUDGET_MAP: dict[ReasoningEffort, int] = {
	"Low": 4096,
	"Medium": 8192,
	"High": 16384,
}


if TYPE_CHECKING:
	from otto.llm.types import Meta, SessionItem, ToolUseUpdate, UserContent


def get_sequence(session: Session) -> list[SessionItem]:
	"""
	Session is defined as a linked list with multiple next nodes (i.e a tree but
	with only one 'active' branch sequence). This converts the linked list into a list
	consisting of the active path.
	"""
	if not session["items"] or not session["first"] or session["first"] not in session["items"]:
		return []

	first = session["items"][session["first"]]
	items = [first]

	while True:
		last = items[-1]

		next = None
		selected_next = last["selected_next"] or 0

		if len(last["next"]) <= selected_next:
			break

		next_id = last["next"][selected_next]
		next = session["items"][next_id]

		items.append(next)

	return items


def get_user_item(content: list[UserContent] | None = None):
	meta: Meta = {
		"role": "user",
		"model": None,
		"input_tokens": 0,
		"output_tokens": 0,
		"cost": 0,
		"timestamp": datetime.datetime.now().timestamp(),
		"start_time": 0,
		"end_time": 0,
		"end_reason": None,
		"time_to_first_chunk": 0,
		"inter_chunk_latency": 0,
	}

	item: SessionItem = {
		"id": uuid.uuid4().hex,
		"next": [],
		"selected_next": 0,
		"content": [],
		"meta": meta,
	}

	if isinstance(content, list):
		item["content"].extend(content)

	return item


def get_agent_item(model: str):
	meta: Meta = {
		"role": "agent",
		"model": model,
		"timestamp": datetime.datetime.now().timestamp(),
		"input_tokens": 0,
		"output_tokens": 0,
		"start_time": 0,
		"end_time": 0,
		"end_reason": None,
		"cost": 0,
		"time_to_first_chunk": 0,
		"inter_chunk_latency": 0,
	}

	item: SessionItem = {
		"id": uuid.uuid4().hex,
		"next": [],
		"selected_next": 0,
		"content": [],
		"meta": meta,
	}

	return item


def get_session(content: list[UserContent] | None, session: Session | None = None) -> Session:
	"""
	Returns an Session with SessionItem containing the query. If session is
	None, a new session is created. Else a copy of the provided session is
	updated and returned.
	"""
	if content is None:
		assert session is not None, "session is required if query is None"
		return json.loads(json.dumps(session))

	item = get_user_item(content)
	if not session:
		session_: Session = {
			"id": uuid.uuid4().hex,
			"items": {item["id"]: item},
			"first": item["id"],
		}
		return session_

	session_ = json.loads(json.dumps(session))
	update_session(
		session_,
		get_last_id(session),
		item,
	)
	return session_


def update_session(session: Session, last_id: str, item: SessionItem) -> None:
	"""
	Updates the session with the new item.
	"""
	last_item = session["items"][last_id]

	assert item["id"] not in last_item["next"], "sanity check"
	last_item["next"].append(item["id"])
	last_item["selected_next"] = len(last_item["next"]) - 1

	assert item["id"] not in session["items"], "sanity check"
	session["items"][item["id"]] = item


def update_tool_use(*, session: Session, update: ToolUseUpdate | list[ToolUseUpdate]) -> None:
	if not isinstance(update, list):
		update = [update]

	update_map = {u["id"]: u for u in update if "id" in u}
	tool_use_ids = set(update_map.keys())
	content_map: dict[str, ToolUseContent] = {}
	for item in session["items"].values():
		for content in item["content"]:
			if content["type"] != "tool_use" or content["id"] not in tool_use_ids:
				continue

			content_map[content["id"]] = content
			tool_use_ids.remove(content["id"])

			if len(tool_use_ids) == 0:
				break

	for id, update in update_map.items():
		content = content_map.get(id)
		if content is None or content["status"] != "pending":
			continue

		result = update.get("result", "")
		if not isinstance(result, str):
			result = json.dumps(result)

		content["status"] = "success" if not update.get("is_error", False) else "error"
		content["result"] = result
		content["stdout"] = update.get("stdout")
		content["stderr"] = update.get("stderr")
		content["start_time"] = update.get("start_time", time.time())
		content["end_time"] = update.get("end_time", time.time())


def get_last_id(session: Session):
	"""
	Walk selected path in item tree to get the last item id.
	Should not be called on an empty sesion.
	"""
	items = session.get("items")
	first = session.get("first")

	assert items is not None and len(items) and first, "sanity check"

	last = items[first]
	while True:
		selected = last["selected_next"]
		if len(last["next"]) <= selected:
			break

		next_id = last["next"][selected]
		last = items[next_id]

	return last["id"]


def get_stats(session: Session) -> SessionStats | None:
	import datetime

	cost = 0
	input_tokens = 0
	output_tokens = 0
	llm_calls = 0
	tools_called: dict[str, SessionToolUseStats] = {}

	latencies = []
	first_chunks = []
	tps = []

	if not session["items"] or not session["first"] or session["first"] not in session["items"]:
		return None

	_start = session["items"][session["first"]]["meta"]["timestamp"]
	_end = session["items"][get_last_id(session)]["meta"]["end_time"]
	start = datetime.datetime.fromtimestamp(_start)
	end = datetime.datetime.fromtimestamp(_end)

	max_input_tokens = 0
	max_output_tokens = 0

	for item in session["items"].values():
		if item["meta"]["role"] == "agent":
			llm_calls += 1

		cost += item["meta"]["cost"]
		input_tokens += item["meta"]["input_tokens"]
		output_tokens += item["meta"]["output_tokens"]

		if item["meta"]["input_tokens"] > max_input_tokens:
			max_input_tokens = item["meta"]["input_tokens"]

		if item["meta"]["output_tokens"] > max_output_tokens:
			max_output_tokens = item["meta"]["output_tokens"]

		if item["meta"]["time_to_first_chunk"] > 0:
			first_chunks.append(item["meta"]["time_to_first_chunk"])

		if item["meta"]["inter_chunk_latency"] > 0:
			latencies.append(item["meta"]["inter_chunk_latency"])

		if item["meta"]["output_tokens"] > 0:
			tps.append(
				item["meta"]["output_tokens"] / (item["meta"]["end_time"] - item["meta"]["start_time"])
			)

		for content_part in item["content"]:
			if content_part["type"] != "tool_use":
				continue
			name = content_part["name"]
			result = content_part["result"]

			if name not in tools_called:
				tools_called[name] = SessionToolUseStats(
					called_count=0,
					error_count=0,
					empty_result_count=0,
				)
			tools_called[name]["called_count"] += 1

			if result is None or result == "" or result == "null" or result == "[]" or result == "{}":
				tools_called[name]["empty_result_count"] += 1

			if content_part["status"] == "error" or (
				isinstance(result, str) and ("Error" in result or "error" in result)
			):
				tools_called[name]["error_count"] += 1

	return SessionStats(
		cost=cost,
		total_input_tokens=input_tokens,
		total_output_tokens=output_tokens,
		start=start.isoformat(),
		end=end.isoformat(),
		duration=(end - start).total_seconds(),
		tools=dict(tools_called),
		max_input_tokens=max_input_tokens,
		max_output_tokens=max_output_tokens,
		llm_calls=llm_calls,
		time_to_first_chunk=sum(first_chunks) / (len(first_chunks) if first_chunks else 1),
		inter_chunk_latency=sum(latencies) / (len(latencies) if latencies else 1),
		tokens_per_second=sum(tps) / (len(tps) if tps else 1),
	)


def is_user_content(data: Any) -> TypeGuard[UserContent]:
	if not isinstance(data, dict):
		return False

	if data.get("type") not in ("text", "image", "file"):
		return False

	if data["type"] == "text":
		return isinstance(data.get("text"), str)

	if data["type"] == "image":
		url = data.get("url")
		img_data = data.get("data")
		return (
			(url is None or isinstance(url, str))
			and (img_data is None or isinstance(img_data, str))
			and (url is not None or img_data is not None)
		)

	if data["type"] == "file":
		return isinstance(data.get("name"), str) and isinstance(data.get("data"), str)

	return False


def to_content(query: Query) -> list[UserContent]:
	"""
	Convenience function to convert list of strings into UserContent, i.e.
	dicts that pertain to image, text or file types.
	"""
	from otto.llm.types import FileContent, ImageContent, TextContent

	if isinstance(query, str):
		return [TextContent(type="text", text=query)]

	if not isinstance(query, list):
		return [query]

	content = []
	for q in query:
		if isinstance(q, dict):
			if is_user_content(q):
				content.append(q)
				continue
			q = utils.json_dumps(q)[0]

		c = TextContent(type="text", text=q)
		if q.startswith("data:application/"):
			c = FileContent(type="file", name="", data=q)

		elif q.startswith("data:image/"):
			c = ImageContent(type="image", data=q, url=None)

		elif q.endswith(".pdf"):
			f = utils.get_file(q, get_data_if_url=True)
			c = FileContent(type="file", name=f.name or "file.pdf", data=f.value)

		elif q.endswith(("png", "jpg", "jpeg")):
			# Will not work for private frappe files
			if q.startswith("http"):
				c = ImageContent(type="image", url=q, data=None)

			else:
				f = utils.get_file(q, get_data_if_url=True)
				c = ImageContent(type="image", data=f.value, url=None)

		content.append(c)
	return content


@contextmanager
def reset_user(force: bool = False):
	user = frappe.local.session.user
	try:
		# Set user may be called somewhere in the callstack of the function that
		# is decorated with this context manager.
		yield
	finally:
		if frappe.local.session.user != user or force:
			assert isinstance(user, str), "sanity check"
			frappe.set_user(user)


def get_provider(model: str) -> Provider | None:
	if model.startswith("openai"):
		return "OpenAI"

	if model.startswith("anthropic"):
		return "Anthropic"

	if model.startswith("gemini"):
		return "Google"

	return None


def get_provider_key(provider: Provider):
	"""API envvar name for the provider's API key. For fieldname in Settings, lowercase the key."""
	match provider:
		case "OpenAI":
			return "OPENAI_API_KEY"
		case "Anthropic":
			return "ANTHROPIC_API_KEY"
		case "Google":
			return "GEMINI_API_KEY"
		case _:
			return None


@utils.cache(ttl=2)
def get_key(provider: Provider) -> tuple[str, str] | tuple[None, None]:
	"""Get API key name and value for provider. Checks envvar and Otto Settings.

	Returns:
		Tuple of (key, value) if found, (None, None) if not found.
	"""
	from frappe.utils.password import get_decrypted_password

	if (key := get_provider_key(provider)) is None:
		return None, None

	password = os.environ.get(key.upper())
	if not password:
		try:
			password = get_decrypted_password("Otto Settings", "Otto Settings", key.lower())
		except Exception:
			password = None

	if password is None:
		return None, None

	return (key, password)
