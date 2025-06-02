from __future__ import annotations

import json

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
		content = json_dumps(content)

	OttoScrapbook.new(content, tool=tool, task=task, execution=execution)


def get_file(url: str):
	"""If url is private or public Frappe File then returns base64 encoded file data else returns as it is"""
	from otto.llm.utils import get_file_content

	assert isinstance(url, str), "url must be a string"

	if url.startswith("data:") or url.startswith("http"):
		return url

	file_url = frappe.get_site_path(url)
	if url.startswith("/"):
		file_url = frappe.get_site_path(url[1:])

	try:
		return get_file_content(file_url)["data"]
	except Exception:
		return url


def get_imgs(html: str):
	"""Extracts all images from given html and returns ImageContents"""
	return []


def get_env(env: dict | None = None):
	"""Global and Task specific env variables"""
	global_env_str = frappe.get_cached_value("Otto Settings", "Otto Settings", "global_env") or "{}"
	global_env = json.loads(global_env_str)
	global_env.update(env or {})
	return frappe._dict(global_env)


def get_lib(env: dict | None = None):
	"""Returned object is available in scripts and code as otto.PROPERTY"""
	return frappe._dict(
		{
			"env": get_env(env),
			"log": log,
			"get_file": get_file,
			"get_imgs": get_imgs,
		}
	)
