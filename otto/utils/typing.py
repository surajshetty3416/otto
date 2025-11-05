from typing import Any


def assert_str(v: Any) -> str:
	assert isinstance(v, str), f"{v} is not str"
	return v
