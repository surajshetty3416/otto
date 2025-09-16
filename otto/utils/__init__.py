from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING, Any

from otto.utils.cache import cache
from otto.utils.file import get_file

__all__ = ["cache", "drain", "get_file", "json_dumps"]

if TYPE_CHECKING:
	from collections.abc import Generator


def json_dumps(value: Any) -> tuple[str, bool]:
	"""
	Use for serializing any value that is to be passed for evaluation or
	session at a later time.
	"""
	try:
		return json.dumps(value, indent=2), True
	except TypeError:
		return json.dumps(value, indent=2, default=_safe_dumps_default), False


def _safe_dumps_default(value: Any):
	if isinstance(value, datetime.datetime):
		return value.isoformat()
	try:
		return str(value)
	except ValueError:
		return "<unserializable>"


# TODO: use this when 3.12 is the minimum
# def drain[T](generator: Generator[Any, None, T]) -> T:
# 	while True:
# 		try:
# 			next(generator)
# 		except StopIteration as e:
# 			return e.value


def drain(generator: Generator[Any, None, Any]) -> Any:
	while True:
		try:
			next(generator)
		except StopIteration as e:
			return e.value


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
