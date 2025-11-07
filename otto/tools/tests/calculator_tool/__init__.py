"""Test package tool for testing sync_tool function with filesystem paths."""

from .operations import add_numbers, multiply_numbers

uid = "test-tools-calculator"
title = "Calculator Tool"
requires_permission = False
use_explanation = False


def calculator(operation: str, x: float, y: float) -> float:
	"""
	Perform a calculation with two numbers.

	Args:
		operation: The operation to perform (add or multiply)
		x: First number
		y: Second number

	Returns:
		The result of the operation
	"""
	if operation == "add":
		return add_numbers(x, y)
	if operation == "multiply":
		return multiply_numbers(x, y)
	raise ValueError(f"Unknown operation: {operation}")
