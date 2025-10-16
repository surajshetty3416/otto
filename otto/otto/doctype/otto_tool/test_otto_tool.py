# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import contextlib

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import UnitTestCase

from otto.otto.doctype.otto_tool.otto_tool import OttoTool


class UnitTestOttoTool(UnitTestCase):
	"""
	Unit tests for OttoTool.
	Use this class for testing individual functions and methods.
	"""

	def setUp(self):
		"""Set up test fixtures."""
		self.created_tools: list[OttoTool] = []

	def tearDown(self):
		"""Clean up created test tools."""
		for tool in self.created_tools:
			with contextlib.suppress(Exception):
				frappe.delete_doc("Otto Tool", tool.name, force=True)

	def test_internal_tool_creation_and_validation(self):
		"""Test creating an internal tool (no code provided) and check if validation works properly."""
		# Create internal tool with valid schema
		tool = OttoTool.new(
			title="Get User Info",
			slug="get_user_info",
			description="Retrieves user information by ID",
			is_external=True,
			args=[
				{
					"arg_name": "user_id",
					"type": "string",
					"description": "The user ID to look up",
					"is_required": True,
				},
				{
					"arg_name": "include_email",
					"type": "boolean",
					"description": "Whether to include email in response",
					"is_required": False,
				},
			],
		)
		self.created_tools.append(tool)

		# Verify tool was created successfully
		self.assertEqual(tool.slug, "get_user_info")
		self.assertEqual(tool.title, "Get User Info")
		self.assertTrue(tool.is_external)
		self.assertTrue(tool.is_valid)
		self.assertIsNone(tool.reason)
		self.assertEqual(len(tool.args), 2)

		# Verify args
		self.assertEqual(tool.args[0].arg_name, "user_id")
		self.assertEqual(tool.args[0].type, "string")
		self.assertTrue(tool.args[0].is_required)
		self.assertEqual(tool.args[1].arg_name, "include_email")
		self.assertEqual(tool.args[1].type, "boolean")
		self.assertFalse(tool.args[1].is_required)

		# Verify schema generation
		schema = tool.get_function_schema()
		self.assertEqual(schema["name"], "get_user_info")
		self.assertEqual(schema["description"], "Retrieves user information by ID")
		self.assertIn("user_id", schema["parameters"]["properties"])
		self.assertIn("include_email", schema["parameters"]["properties"])
		self.assertIn("user_id", schema["parameters"]["required"])
		self.assertNotIn("include_email", schema["parameters"]["required"])

	def test_internal_tool_validation_failure(self):
		"""Test internal tool validation fails when description is missing."""
		tool = OttoTool.new(
			title="Invalid Tool",
			slug="invalid_tool",
			is_external=True,
			args=[
				{
					"arg_name": "param1",
					"type": "string",
					"is_required": True,
				}
			],
		)
		self.created_tools.append(tool)

		# Should be invalid due to missing descriptions
		self.assertFalse(tool.is_valid)
		self.assertIsNotNone(tool.reason)
		assert tool.reason is not None  # for type checker
		self.assertIn("description missing", tool.reason.lower())

	def test_internal_tool_cannot_execute(self):
		"""Test that internal tools cannot be executed."""
		tool = OttoTool.new(
			title="Internal Tool",
			slug="internal_tool",
			description="An internal tool",
			is_external=True,
			args=[
				{
					"arg_name": "name",
					"type": "string",
					"description": "The name parameter",
					"is_required": True,
				}
			],
		)
		self.created_tools.append(tool)

		# Attempting to execute should raise ValidationError
		with self.assertRaises(ValidationError) as context:
			tool.execute({"name": "test"})

		self.assertIn("Internal tools cannot be executed", str(context.exception))

	def test_non_internal_tool_with_code_auto_detect(self):
		"""Test creating a non-internal tool with code and auto-detecting args."""
		code = """
def main(a: int, b: int, verbose: bool = False):
	result = a + b
	if verbose:
		return {"sum": result, "details": f"{a} + {b} = {result}"}
	return result
"""

		tool = OttoTool.new(
			title="Calculate Sum",
			slug="calculate_sum",
			code=code,
		)
		self.created_tools.append(tool)

		# Tool should be invalid initially (missing descriptions)
		self.assertFalse(tool.is_valid)
		self.assertIsNotNone(tool.reason)

		# But args should be detected
		self.assertEqual(len(tool.args), 3)
		arg_names = [arg.arg_name for arg in tool.args]
		self.assertIn("a", arg_names)
		self.assertIn("b", arg_names)
		self.assertIn("verbose", arg_names)

		# Check arg types were inferred correctly
		for arg in tool.args:
			if arg.arg_name == "a" or arg.arg_name == "b":
				self.assertEqual(arg.type, "integer")
				self.assertTrue(arg.is_required)
			elif arg.arg_name == "verbose":
				self.assertEqual(arg.type, "boolean")
				self.assertFalse(arg.is_required)

		# Now add descriptions to make it valid
		tool.description = "Calculates the sum of two numbers"
		for arg in tool.args:
			if arg.arg_name == "a":
				arg.description = "First number"
			elif arg.arg_name == "b":
				arg.description = "Second number"
			elif arg.arg_name == "verbose":
				arg.description = "Whether to return detailed output"
		tool.save()

		# Reload and verify it's valid now
		tool.reload()
		self.assertTrue(tool.is_valid)
		self.assertIsNone(tool.reason)

	def test_non_internal_tool_with_explicit_details(self):
		"""Test creating a non-internal tool with code and explicit details."""
		code = """
def main(x: float, y: float):
	return x * y
"""

		tool = OttoTool.new(
			title="Multiply Numbers",
			slug="multiply_numbers",
			description="Multiplies two numbers together",
			code=code,
		)
		self.created_tools.append(tool)

		# Add explicit descriptions for args
		tool.description = "Multiplies two numbers and returns the result"
		for arg in tool.args:
			if arg.arg_name == "x":
				arg.description = "The first number to multiply"
			elif arg.arg_name == "y":
				arg.description = "The second number to multiply"
		tool.save()

		# Reload and verify
		tool.reload()
		self.assertTrue(tool.is_valid)
		self.assertIsNone(tool.reason)
		self.assertEqual(len(tool.args), 2)

		# Verify explicit details were set
		self.assertEqual(tool.description, "Multiplies two numbers and returns the result")
		for arg in tool.args:
			self.assertIsNotNone(arg.description)
			if arg.arg_name == "x":
				self.assertEqual(arg.description, "The first number to multiply")
				self.assertEqual(arg.type, "number")
			elif arg.arg_name == "y":
				self.assertEqual(arg.description, "The second number to multiply")
				self.assertEqual(arg.type, "number")

	def test_execute_non_internal_tool_simple(self):
		"""Test executing a simple non-internal tool."""
		code = """
def main(a: int, b: int):
	return a + b
"""

		tool = OttoTool.new(
			title="Add Numbers",
			slug="add_numbers",
			description="Adds two numbers",
			code=code,
		)
		self.created_tools.append(tool)

		# Add descriptions
		for arg in tool.args:
			if arg.arg_name == "a":
				arg.description = "First number"
			elif arg.arg_name == "b":
				arg.description = "Second number"
		tool.save()
		tool.reload()

		# Execute the tool
		result = tool.execute({"a": 5, "b": 3})

		# Verify result
		self.assertEqual(result["result"], 8)
		self.assertEqual(result["stdout"], "")
		self.assertEqual(result["stderr"], "")

	def test_execute_non_internal_tool_with_otto_lib(self):
		"""Test executing a tool that uses the otto library."""
		code = """
def main(message: str):
	# Test using the otto library's log function and env
	otto.log(message, tool=refs.tool)
	env_data = otto.env
	return {"message": message, "has_env": bool(env_data)}
"""

		tool = OttoTool.new(
			title="Test Otto Library",
			slug="test_otto_library",
			description="Tests the otto library functions",
			code=code,
		)
		self.created_tools.append(tool)

		# Add descriptions
		for arg in tool.args:
			if arg.arg_name == "message":
				arg.description = "A message to log"
		tool.save()
		tool.reload()

		# Execute the tool
		result = tool.execute({"message": "test"})

		# Verify result (should return a dict with message and env info)
		self.assertIsNotNone(result["result"])
		self.assertIsInstance(result["result"], dict)
		self.assertEqual(result["result"]["message"], "test")
		self.assertTrue(result["result"]["has_env"])

	def test_execute_non_internal_tool_with_default_args(self):
		"""Test executing a tool with default arguments."""
		code = """
def main(name: str, greeting: str = "Hello"):
	return f"{greeting}, {name}!"
"""

		tool = OttoTool.new(
			title="Greet User",
			slug="greet",
			description="Greets a user with a customizable greeting",
			code=code,
		)
		self.created_tools.append(tool)

		# Add descriptions
		for arg in tool.args:
			if arg.arg_name == "name":
				arg.description = "The name to greet"
			elif arg.arg_name == "greeting":
				arg.description = "The greeting to use"
		tool.save()
		tool.reload()

		# Execute with only required arg
		result1 = tool.execute({"name": "Alice"})
		self.assertEqual(result1["result"], "Hello, Alice!")

		# Execute with both args
		result2 = tool.execute({"name": "Bob", "greeting": "Hi"})
		self.assertEqual(result2["result"], "Hi, Bob!")

	def test_mock_tool_execution(self):
		"""Test executing a mock tool."""
		tool = OttoTool.new(
			title="Mock Tool",
			slug="mock_tool",
			description="A mock tool for testing",
			code="def main(): pass",
			mock_tool=True,
			mock_return_value='{"status": "success", "value": 42}',
		)
		self.created_tools.append(tool)
		tool.save()
		tool.reload()

		# Execute the mock tool
		result = tool.execute({})

		# Verify mock result
		self.assertEqual(result["result"]["status"], "success")
		self.assertEqual(result["result"]["value"], 42)

	def test_tool_with_use_explanation(self):
		"""Test tool with use_explanation flag adds explanation to schema."""
		tool = OttoTool.new(
			title="Tool With Explanation",
			slug="tool_with_explanation",
			description="A tool that requires explanation",
			use_explanation=True,
			is_external=True,
			args=[
				{
					"arg_name": "param1",
					"type": "string",
					"description": "A parameter",
					"is_required": True,
				}
			],
		)
		self.created_tools.append(tool)

		# Get schema
		schema = tool.get_function_schema()

		# Verify explanation is in schema
		self.assertIn("explanation", schema["parameters"]["properties"])
		self.assertIn("explanation", schema["parameters"]["required"])
		self.assertEqual(schema["parameters"]["properties"]["explanation"]["type"], "string")

	def test_tool_validation_invalid_code(self):
		"""Test that invalid code makes tool invalid."""
		# Test with missing main function
		code_no_main = """
def other_function(a: int):
	return a + 1
"""

		tool = OttoTool.new(
			title="Invalid Code Tool",
			slug="invalid_code_tool",
			description="Tool with invalid code",
			code=code_no_main,
		)
		self.created_tools.append(tool)

		# Tool should be invalid due to missing main function
		self.assertFalse(tool.is_valid)
		self.assertIsNotNone(tool.reason)
		assert tool.reason is not None  # for type checker
		self.assertIn("main", tool.reason.lower())

	def test_tool_title_slug_auto_generation(self):
		"""Test automatic generation of title from slug and vice versa."""
		# Test slug generation from title
		tool1 = OttoTool.new(
			title="My Cool Tool",
			description="A cool tool",
			is_external=True,
			args=[],
		)
		self.created_tools.append(tool1)
		self.assertEqual(tool1.slug, "my_cool_tool")

		# Test title generation from slug
		tool2 = OttoTool.new(
			slug="another_awesome_tool",
			description="Another awesome tool",
			is_external=True,
			args=[],
		)
		self.created_tools.append(tool2)
		self.assertEqual(tool2.title, "Another Awesome Tool")
