"""Test assistant that uses mixed tool specification methods."""

from otto.assistants.test import simple_tool
from otto.assistants.utils import get_tool

uid = "test-mixed-tools-assistant"
name = "Mixed Tools Test Assistant"
dev_mode_only = False

instruction = "Test assistant using mixed tool specification methods."


def multiply(a: int, b: int) -> int:
	"""
	Multiply two numbers.

	Args:
		a (int): First number
		b (int): Second number

	Returns:
		int: Product of the two numbers
	"""
	return a * b


# Create a ToolDefinition using get_tool
multiply_tool = get_tool(
	multiply,
	uid="test-mixed-tools-multiply",
	title="Multiply Numbers",
)

# Tools specified using all three methods:
# 1. ToolDefinition object (multiply_tool)
# 2. Module object (simple_tool)
# 3. String path to module
tools = [
	multiply_tool,  # ToolDefinition
	simple_tool,  # Module object
	"otto.assistants.test.simple_tool",  # String path
]
