"""Test tool with requires_permission for testing sync_tool function."""

uid = "test-tools-multiply"
title = "Multiply Numbers"
requires_permission = True
use_explanation = True


def multiply(x: int, y: int) -> int:
	"""
	Multiply two numbers.

	Args:
		x (int): First number
		y (int): Second number

	Returns:
		int: Product of the two numbers
	"""
	return x * y
