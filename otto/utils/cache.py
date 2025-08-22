from __future__ import annotations

import functools
import time


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
