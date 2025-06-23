from __future__ import annotations

import json
from urllib.parse import urlparse

import frappe

from otto.utils import json_dumps

"""
Code in this is passed as library code to tool execution as globals.
"""

from typing import Any


def log(
	content: Any,
	*,
	tool: str | None = None,
	task: str | None = None,
	execution: str | None = None,
):
	"""Creates a new scrapbook entry"""

	from otto.otto.doctype.otto_scrapbook.otto_scrapbook import OttoScrapbook

	if not isinstance(content, str):
		content = json_dumps(content)[0]

	OttoScrapbook.new(content, tool=tool, task=task, execution=execution)


def get_file(url: str):
	"""If url is private or public Frappe File then returns base64 encoded file data else returns as it is"""

	from otto.llm.utils import get_file_content

	assert isinstance(url, str), "url must be a string"
	parsed = urlparse(url)

	if parsed.scheme in ("http", "https", "data"):
		return url

	files = frappe.get_all("File", filters={"file_url": parsed.path}, pluck="name", limit=1)
	if not files and parsed.query:
		files = [q.split("=")[1].strip() for q in parsed.query.split("&") if q.startswith("fid=")]
		files = [f for f in files if f]

	try:
		from frappe.core.doctype.file.file import File

		import otto

		path = otto.get(File, files[0]).get_full_path()
		assert isinstance(path, str), "unsafe type check"
		return get_file_content(path)["data"]
	except Exception:
		return url


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
		content.append(get_file(str(img.get("src")))) # type: ignore
		last_idx = end_idx

	content.append(html[last_idx:])
	return [c for c in content if c]


def get_env(env: dict | None = None):
	"""Global and Task specific env variables"""
	global_env_str = frappe.get_cached_value("Otto Settings", "Otto Settings", "global_env") or "{}"
	global_env = json.loads(global_env_str)
	global_env.update(env or {})
	return frappe._dict(global_env)


def to_html(content: str):
	"""Converts provided markdown to HTML"""
	from markdown2 import markdown

	extras = {
		"fenced-code-blocks": None,
		"tables": None,
		"strike": None,
		"cuddled-lists": None,
		"footnotes": None,
		"header-ids": None,
		"target-blank-links": None,
		"html-classes": {"table": "table table-bordered", "img": "screenshot"},
	}

	return markdown(content, extras=extras)


def get_lib(env: dict | None = None):
	"""Returned object is available in scripts and code as otto.PROPERTY"""
	return frappe._dict(
		{
			"env": get_env(env),
			"log": log,
			"get_file": get_file,
			"interpolate_imgs": interpolate_imgs,
			"to_html": to_html,
		}
	)
