"""Test tool for testing sync_tool function."""

uid = "test-tools-add"
title = "Add Numbers"
requires_permission = False


def add(a: int, b: int) -> int:
	"""
	Add two numbers together.

	Args:
		a (int): First number
		b (int): Second number

	Returns:
		int: Sum of the two numbers
	"""
	return a + b
