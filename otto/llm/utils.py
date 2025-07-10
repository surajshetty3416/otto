from __future__ import annotations

import base64
import datetime
import json
import mimetypes
import os
import uuid
from typing import TYPE_CHECKING, Any, TypeGuard
from urllib.parse import urlparse
from urllib.request import urlopen

from otto.llm.types import Session
from otto.utils import json_dumps

if TYPE_CHECKING:
	from otto.llm.types import Session, SessionItem, SessionMeta, UserContent


def get_session_list(session: Session) -> list[SessionItem]:
	"""
	Session is defined as a linked list with multiple next nodes (i.e a tree but
	with only one 'active' branch sequence). This converts the linked list into a list
	consisting of the active path.
	"""
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
	meta: SessionMeta = {
		"role": "user",
		"model": None,
		"input_tokens": 0,
		"output_tokens": 0,
		"cost": 0,
		"timestamp": datetime.datetime.now().timestamp(),
		"start_time": 0,
		"end_time": 0,
		"end_reason": None,
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
	meta: SessionMeta = {
		"role": "agent",
		"model": model,
		"timestamp": datetime.datetime.now().timestamp(),
		"input_tokens": 0,
		"output_tokens": 0,
		"start_time": 0,
		"end_time": 0,
		"end_reason": None,
		"cost": 0,
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


def update_with_tool_result(*, session: Session, result: Any, id: str, is_error: bool = False) -> None:
	for item in session["items"].values():
		for part in item["content"]:
			if part["type"] != "tool_use" or part["id"] != id:
				continue

			if not isinstance(result, str):
				result = json.dumps(result)

			part["result"] = result
			part["status"] = "success" if not is_error else "error"
			return


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


def get_stats(session: Session):
	import datetime

	cost = 0
	input_tokens = 0
	output_tokens = 0
	llm_calls = 0
	tools_called = {}

	_start = session["items"][session["first"]]["meta"]["timestamp"]
	_end = session["items"][get_last_id(session)]["meta"]["end_time"]
	start = datetime.datetime.fromtimestamp(_start)
	end = datetime.datetime.fromtimestamp(_end)

	max_input_tokens = 0
	max_output_tokens = 0

	for item in session["items"].values():
		llm_calls += 1
		cost += item["meta"]["cost"]
		input_tokens += item["meta"]["input_tokens"]
		output_tokens += item["meta"]["output_tokens"]

		if item["meta"]["input_tokens"] > max_input_tokens:
			max_input_tokens = item["meta"]["input_tokens"]
		if item["meta"]["output_tokens"] > max_output_tokens:
			max_output_tokens = item["meta"]["output_tokens"]

		for content_part in item["content"]:
			if content_part["type"] != "tool_use":
				continue
			name = content_part["name"]
			result = content_part["result"]

			if name not in tools_called:
				tools_called[name] = {
					"called_count": 0,
					"empty_result_count": 0,
					"error_count": 0,
				}
			tools_called[name]["called_count"] += 1

			if result is None or result == "" or result == "null" or result == "[]" or result == "{}":
				tools_called[name]["empty_result_count"] += 1

			if (
				content_part["status"] == "error"
				or isinstance(result, str)
				and ("Error" in result or "error" in result)
			):
				tools_called[name]["error_count"] += 1

	return dict(
		cost=cost,
		total_input_tokens=input_tokens,
		total_output_tokens=output_tokens,
		start=start.isoformat(),
		end=end.isoformat(),
		duration=end - start,
		tools=dict(tools_called),
		max_input_tokens=max_input_tokens,
		max_output_tokens=max_output_tokens,
		llm_calls=llm_calls - 1,
	)


def get_file_content(file_path_or_url: str) -> dict[str, str]:
	"""
	Takes a URL or path to a file and returns a dictionary with the file's
	contents in base64 (including mime type prefix) and its filename.

	Args:
		file_path_or_url: A string representing either a local file path or a URL

	Returns:
		A dictionary containing:
			- 'filename': The name of the file
			- 'file_data': The base64-encoded content of the file with mime type prefix
	"""
	filename, mime_type, content = _get_content(file_path_or_url)
	base64_content = base64.b64encode(content).decode("utf-8")
	return {
		"name": filename,
		"data": f"data:{mime_type};base64,{base64_content}",
	}


def _get_content(file_path_or_url: str):
	parsed_url = urlparse(file_path_or_url)

	if parsed_url.scheme in ("http", "https"):
		with urlopen(file_path_or_url) as response:
			content = response.read()

		filename = os.path.basename(parsed_url.path) or "downloaded_file"
		mime_type = response.info().get_content_type()
		return filename, mime_type, content

	# Handle local file path
	with open(file_path_or_url, "rb") as file:
		content = file.read()

	filename = os.path.basename(file_path_or_url)
	mime_type, _ = mimetypes.guess_type(file_path_or_url)
	if mime_type is None:
		mime_type = "application/octet-stream"

	return filename, mime_type, content


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


def to_content(query: str | list[Any]) -> list[UserContent]:
	"""
	Convenience function to convert list of strings into UserContent, i.e.
	dicts that pertain to image, text or file types.
	"""
	from otto.llm.types import FileContent, ImageContent, TextContent

	if isinstance(query, str):
		return [TextContent(type="text", text=query)]

	content = []
	for q in query:
		if isinstance(q, dict):
			if is_user_content(q):
				content.append(q)
				continue
			else:
				q = json_dumps(q)[0]

		c = TextContent(type="text", text=q)
		if q.startswith("data:application/"):
			c = FileContent(type="file", name="", data=q)

		elif q.startswith("data:image/"):
			c = ImageContent(type="image", data=q, url=None)

		elif q.endswith(".pdf"):
			d = get_file_content(q)
			c = FileContent(type="file", name=d["name"], data=d["data"])

		elif q.endswith(("png", "jpg", "jpeg")):
			# Will not work for private frappe files
			if q.startswith("http"):
				c = ImageContent(type="image", url=q, data=None)

			else:
				d = get_file_content(q)
				c = ImageContent(type="image", data=d["data"], url=None)

		content.append(c)
	return content
