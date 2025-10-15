from __future__ import annotations

import json
from contextlib import suppress
from typing import TypeGuard

import frappe

from otto import Any, utils
from otto.lib.types import FileContent, ImageContent, ReasoningEffort, TextContent, ToolUseContent


class content:
	"""
	Convenience class for creating `UserContent` objects.

	Examples:
	```python
	from otto.lib import content
	from otto.lib import quick_query

	# Create a list of user content objects
	user_content = [
	    # Text content
	    content.text("Hello, can you explain these images and files?"),
	    # Image content from url
	    content.image("https://example.com/image.png"),
	    # File content
	    content.file("data:application/pdf;base64,...", name="document.pdf"),
	    # Image content from data
	    content.image("data:image/png;base64,..."),
	]


	# Call the LLM
	res = quick_query(user_content)
	```
	"""

	@staticmethod
	def text(query: str) -> TextContent:
		"""
		Create a text content object.

		Args:
			query: The text to be displayed.
		"""
		return TextContent(type="text", text=query)

	@staticmethod
	def image(value: str) -> ImageContent:
		"""
		Create an image content object from various sources.

		Args:
			value: The image source, which can be:
				- HTTP/HTTPS URL (e.g., "https://example.com/image.png")
				- Data URI (e.g., "data:image/png;base64,...")
				- Frappe File document name or file URL
				- Local file path
		"""
		f = utils.get_file(value, get_data_if_url=False)
		if f.is_url:
			return ImageContent(type="image", url=f.value, data=None)
		return ImageContent(type="image", data=f.value, url=None)

	@staticmethod
	def file(value: str, name: str | None = None) -> FileContent:
		"""
		Create a file content object from various sources.

		Args:
			value: The file source, which can be:
				- HTTP/HTTPS URL (e.g., "https://example.com/document.pdf")
				- Data URI (e.g., "data:application/pdf;base64,...")
				- Frappe File document name or file URL
				- Local file path
			name: The name of the file. If not provided, will be inferred from the source.
		"""
		f = utils.get_file(value, get_data_if_url=True)
		return FileContent(
			type="file",
			name=name or f.name or "file.pdf",
			data=f.value,
		)


def get_tool_uses(
	*,
	session: str | list[str] | None = None,
	id: str | list[str] | None = None,
	status: str | list[str] | None = None,
	name: str | list[str] | None = None,
	limit: int = 0,
) -> list[tuple[str, ToolUseContent]]:
	"""Get a list of tuple[session_id, ToolUseContent] filtered by the given args"""

	query = """
		SELECT
			osi.parent as session,
			jt.id,
			jt.type,
			jt.name,
			jt.args,
			jt.override,
			jt.status,
			jt.result,
			jt.start_time,
			jt.end_time,
			jt.stdout,
			jt.stderr
		FROM `tabOtto Session Item CT` osi,
		JSON_TABLE(
			osi.content, '$[*]' COLUMNS(
				id TEXT PATH '$.id',
				type TEXT PATH '$.type',
				name TEXT PATH '$.name',
				args JSON PATH '$.args',
				override JSON PATH '$.override',
				status TEXT PATH '$.status',
				result TEXT PATH '$.result',
				start_time FLOAT PATH '$.start_time',
				end_time FLOAT PATH '$.end_time',
				stdout TEXT PATH '$.stdout',
				stderr TEXT PATH '$.stderr'
			)
		) AS jt
		WHERE jt.type = 'tool_use'
	"""
	params: list = []

	# Handle session_id (str or list[str] or None)
	if session is not None:
		if isinstance(session, list):
			query += f" AND osi.parent IN ({', '.join(['%s'] * len(session))})"
			params.extend(session)
		else:
			query += " AND osi.parent = %s"
			params.append(session)

	# Handle id filter
	if id is not None:
		if isinstance(id, list):
			query += f" AND jt.id IN ({', '.join(['%s'] * len(id))})"
			params.extend(id)
		else:
			query += " AND jt.id = %s"
			params.append(id)

	# Handle status filter
	if status is not None:
		if isinstance(status, list):
			query += f" AND jt.status IN ({', '.join(['%s'] * len(status))})"
			params.extend(status)
		else:
			query += " AND jt.status = %s"
			params.append(status)

	# Handle name filter
	if name is not None:
		if isinstance(name, list):
			query += f" AND jt.name IN ({', '.join(['%s'] * len(name))})"
			params.extend(name)
		else:
			query += " AND jt.name = %s"
			params.append(name)

	if limit > 0:
		query += f"\nLIMIT {limit}"

	result: list[dict] = frappe.db.sql(
		query,
		params,
		as_dict=True,
	)  # pyright: ignore[reportAssignmentType]

	if not result:
		return []

	uses: list[tuple[str, ToolUseContent]] = []

	for row in result:
		args = {}
		override = None
		if row["args"]:
			args = json.loads(row["args"])

		if o := row.get("override"):
			with suppress(json.JSONDecodeError):
				override = json.loads(o)

		session = row["session"]
		assert isinstance(session, str), "type check"

		tool_use = ToolUseContent(
			type="tool_use",
			id=row["id"],
			name=row["name"],
			args=args,
			override=override,
			status=row["status"],
			result=row["result"],
			start_time=row["start_time"] or 0.0,
			end_time=row["end_time"] or 0.0,
			stdout=row["stdout"],
			stderr=row["stderr"],
		)
		uses.append((session, tool_use))
	return uses


def get_tool_use(
	session: str,
	tool_use_id: str,
) -> ToolUseContent | None:
	"""Get a specific ToolUseContent by its ID from a Session."""
	if uses := get_tool_uses(session=session, id=tool_use_id, limit=1):
		return uses[0][1]

	return None


def to_html(content: str):
	"""Converts provided markdown to HTML"""
	from otto.utils import to_html

	return to_html(content)


def get_file(url: str):
	"""If url is private or public Frappe File then returns base64 encoded file data else returns as it is"""

	assert isinstance(url, str), "url must be a string"
	return utils.get_file(url, get_data_if_url=False).value


def interpolate_imgs(html: str):
	"""
	Interpolate img urls within images, the images can then be converted
	into the right content types.

	Eg:
		from: '<div><img src="file.png"></div>'
		to: ['from: '<div><img src="file.png">', 'file.png' , '</div>']
	"""
	from bs4 import BeautifulSoup

	soup = BeautifulSoup(html, "html.parser")
	if not (imgs := soup.find_all("img")):
		return [html]

	content = []
	last_idx = 0
	for img in imgs:
		start_idx = html.find("<img", last_idx)

		if start_idx == -1:
			continue

		end_idx = html.find(">", start_idx) + 1
		content.append(html[last_idx:end_idx])

		# get image
		content.append(get_file(str(img.get("src"))))  # type: ignore
		last_idx = end_idx

	content.append(html[last_idx:])
	return [c for c in content if c]


def is_reasoning_effort(value: Any) -> TypeGuard[ReasoningEffort]:
	"""Type guard to check if a value is a valid ReasoningEffort."""
	return value in ["Low", "Medium", "High"]
