from __future__ import annotations

import datetime
import functools
import json
import time
from collections.abc import Generator
from typing import Any


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


def cache(ttl: int = 1):
	"""Least-recently-used cache decorator with time-to-live (TTL).

	A decorator that caches function results using LRU caching strategy and automatically
	invalidates the cache after the specified TTL period has elapsed.

	Args:
		ttl: Time-to-live in seconds before the cache is cleared. Defaults to 1 second.

	Returns:
		A decorator function that will cache the decorated function's results.

	Example:
		@cache(ttl=60)
		def expensive_function(x, y):
			# Results will be cached for 60 seconds
			return x + y
	"""

	def decorator(func):
		lru_wrapped = functools.lru_cache(maxsize=None)(func)

		timestamp = {"now": time.monotonic()}

		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			now = time.monotonic()
			if now - timestamp["now"] > ttl:
				lru_wrapped.cache_clear()

			timestamp["now"] = now
			return lru_wrapped(*args, **kwargs)

		return wrapper

	return decorator
