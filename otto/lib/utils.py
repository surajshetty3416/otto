from __future__ import annotations

import json

import frappe

from otto import utils
from otto.lib.types import FileContent, ImageContent, TextContent, ToolUseContent


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


def get_tool_use(session_id: str, tool_use_id: str) -> ToolUseContent | None:
	"""Get a specific ToolUseContent by its ID from a Session."""
	query = """
		SELECT
			jt.id,
			jt.type,
			jt.name,
			jt.args,
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
				status TEXT PATH '$.status',
				result TEXT PATH '$.result',
				start_time FLOAT PATH '$.start_time',
				end_time FLOAT PATH '$.end_time',
				stdout TEXT PATH '$.stdout',
				stderr TEXT PATH '$.stderr'
			)
		) AS jt
		WHERE osi.parent = %s
		AND jt.type = 'tool_use'
		AND jt.id = %s
		LIMIT 1
	"""

	result: list[dict] = frappe.db.sql(
		query,
		[session_id, tool_use_id],
		as_dict=True,
	)  # pyright: ignore[reportAssignmentType]

	if not result:
		return None

	row = result[0]
	args = {}
	if row["args"]:
		args = json.loads(row["args"])

	return ToolUseContent(
		type="tool_use",
		id=row["id"],
		name=row["name"],
		args=args,
		status=row["status"],
		result=row["result"],
		start_time=row["start_time"] or 0.0,
		end_time=row["end_time"] or 0.0,
		stdout=row["stdout"],
		stderr=row["stderr"],
	)
