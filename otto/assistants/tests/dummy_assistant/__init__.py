from __future__ import annotations

from otto.assistants.utils import get_tool

uid = "test-dummy-assistant"
name = "Test Dummy Assistant"
dev_mode_only = False

instruction = "You are a test assistant that can perform simple calculations and echo messages."


def add_numbers(a: int, b: int) -> int:
	"""
	Add two numbers together.

	Args:
		a (int): First number
		b (int): Second number

	Returns:
		int: Sum of the two numbers
	"""
	return a + b


def echo_message(message: str) -> str:
	"""
	Echo back the provided message.

	Args:
		message (str): The message to echo

	Returns:
		str: The same message
	"""
	return message


add_tool = get_tool(
	add_numbers,
	uid="test-dummy-assistant-add",
	title="Add Numbers",
)

echo_tool = get_tool(
	echo_message,
	uid="test-dummy-assistant-echo",
	title="Echo Message",
	requires_permission=False,
)

tools = [add_tool, echo_tool]


def get_context():
	return {"test_value": "dummy_context"}
