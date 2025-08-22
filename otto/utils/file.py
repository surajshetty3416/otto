from __future__ import annotations

import base64
import mimetypes
import os
from typing import TYPE_CHECKING, NamedTuple
from urllib.request import urlopen

import frappe
from frappe.exceptions import DoesNotExistError

from otto.utils.cache import cache

if TYPE_CHECKING:
	from urllib.parse import ParseResult


class File(NamedTuple):
	name: str | None  # File name if exists
	value: str  # Base64 encoded data or URL
	is_url: bool  # Whether value is a URL


@cache(ttl=60)  # Left at 60 cause potentially a bad idea
def get_file(
	value: str,
	get_data_if_url: bool = False,
) -> File:
	"""
	Get file content from various sources and return as a File object.

	This function handles:
	- Data URIs (data:...)
	- HTTP/HTTPS URLs
	- Frappe File documents
	- Local file paths

	Args:
		value: The file identifier - can be a URL, file path, data URI, or Frappe File name/URL
		get_data_if_url: Whether to download content from HTTP/HTTPS URLs and return base64 data.

	Returns:
		File: A named tuple containing:
			- name: The filename if available, None otherwise
			- value: Base64 encoded data URI or the original URL
			- is_url: True if the value is a URL, False if it's base64 data

	Raises:
		ValueError: If the value is not a valid URL, path, data URI, or Frappe File
	"""

	from urllib.parse import urlparse

	parsed = urlparse(value)
	if parsed.scheme == "data":
		return File(name=None, value=value, is_url=False)

	is_url = parsed.scheme in ("http", "https")
	if is_url and not get_data_if_url:
		return File(name=None, value=value, is_url=is_url)

	if is_url:
		return _get_file_content_from_url(value, parsed)

	if file := _get_file_content_from_frappe_file(parsed):
		return file

	if file := _get_file_from_file_path(value):
		return file

	raise ValueError(f'value "{value}" is not a valid URL, path, base64 data URI, or Frappe File')


def _get_file_content_from_url(url: str, parsed: ParseResult):
	with urlopen(url) as response:
		content = response.read()

	filename = os.path.basename(parsed.path) or "file"  # better fallback?
	mime_type = response.info().get_content_type()
	b64_data = base64.b64encode(content).decode("utf-8")

	return File(
		name=filename,
		value=f"data:{mime_type};base64,{b64_data}",
		is_url=False,
	)


def _get_file_content_from_frappe_file(parsed: ParseResult):
	files = frappe.get_all(
		"File",
		filters={"file_url": parsed.path},
		pluck="name",
		limit=1,
	)
	if not files and parsed.query:
		files = [q.split("=")[1].strip() for q in parsed.query.split("&") if q.startswith("fid=")]
		files = [f for f in files if f]

	if not files:
		files = [parsed.path]

	try:
		from frappe.core.doctype.file.file import File

		import otto

		path = otto.get(File, files[0]).get_full_path()
	except DoesNotExistError:
		return None

	if not path or not isinstance(path, str):
		return None

	return _get_file_from_file_path(path)


def _get_file_from_file_path(path: str):
	try:
		with open(path, "rb") as file:
			content = file.read()
	except FileNotFoundError:
		return None

	filename = os.path.basename(path)
	mimetype, _ = mimetypes.guess_type(path)
	if mimetype is None:
		mimetype = "application/octet-stream"

	return File(
		name=filename,
		value=f"data:{mimetype};base64,{base64.b64encode(content).decode('utf-8')}",
		is_url=False,
	)
