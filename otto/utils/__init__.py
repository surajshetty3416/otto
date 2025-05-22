from __future__ import annotations

import json
from typing import Any


def json_dumps(value: Any) -> tuple[str, bool]:
	"""
	Use for serializing any value that is to be passed for evaluation or
	execution at a later time.
	"""
	try:
		return json.dumps(value, indent=2), True
	except TypeError:
		return json.dumps(value, indent=2, default=_safe_dumps_default), False


def _safe_dumps_default(value: Any):
	# if isinstance(value, Document):
	# 	return f"{value.doctype}#{value.name}"
	try:
		return str(value)
	except ValueError:
		return "<unserializable>"
