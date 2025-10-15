from __future__ import annotations

import json
from typing import Any

import frappe

from otto import utils

"""
Code in this is passed as library code to tool session as globals.
"""


def log(
	content: Any,
	*,
	tool: str | None = None,
	task: str | None = None,
	session: str | None = None,
):
	"""Creates a new scrapbook entry"""

	from otto.otto.doctype.otto_scrapbook.otto_scrapbook import OttoScrapbook

	if not isinstance(content, str):
		content = utils.json_dumps(content)[0]

	OttoScrapbook.new(content, tool=tool, task=task, session=session)


def get_env(env: dict | None = None):
	"""Global and Task specific env variables"""
	global_env_str = frappe.get_cached_value("Otto Settings", "Otto Settings", "global_env") or "{}"
	global_env = json.loads(global_env_str)
	global_env.update(env or {})
	return frappe._dict(global_env)


def set_user(user: str):
	"""Sets the current user for the session"""
	frappe.set_user(user)


def get_lib(env: dict | None = None):
	from otto.lib.utils import get_file, interpolate_imgs, to_html

	"""Returned object is available in scripts and code as otto.PROPERTY"""
	return frappe._dict(
		{
			"env": get_env(env),
			"log": log,
			"get_file": get_file,
			"to_html": to_html,
			"set_user": set_user,
			"interpolate_imgs": interpolate_imgs,
		}
	)
