# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import contextlib

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import UnitTestCase

from otto.otto.doctype.otto_tool.otto_tool import OttoTool


# Helper function for testing tool_import_path
def test_import_function(x: int, y: int) -> dict:
	"""A simple function to test tool_import_path functionality."""
	return {"sum": x + y, "product": x * y}


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

	def test_external_tool_creation_and_validation(self):
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

	def test_external_tool_validation_failure(self):
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

	def test_external_tool_cannot_execute(self):
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

		self.assertIn("External tools must be", str(context.exception))

	def test_tool_with_code_auto_detect(self):
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

	def test_tool_with_explicit_details(self):
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

	def test_execute_tool_simple(self):
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

	def test_execute_tool_with_otto_lib(self):
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

	def test_execute_tool_with_default_args(self):
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

	def test_external_tool_execution_with_function(self):
		"""Test executing an external tool with a simple function."""
		# Create external tool
		tool = OttoTool.new(
			title="Add Numbers External",
			slug="add_numbers_external",
			description="Adds two numbers using external function",
			is_external=True,
			args=[
				{
					"arg_name": "a",
					"type": "integer",
					"description": "First number",
					"is_required": True,
				},
				{
					"arg_name": "b",
					"type": "integer",
					"description": "Second number",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(tool)

		# Define a simple add function
		def add_fn(a: int, b: int):
			return a + b

		# Execute the tool with the function
		result = tool.execute({"a": 10, "b": 5}, fn=add_fn)

		# Verify result
		self.assertEqual(result["result"], 15)
		self.assertEqual(result["stdout"], "")
		self.assertEqual(result["stderr"], "")

	def test_external_tool_execution_with_execute_tool(self):
		"""Test executing an external tool using the execute_tool function."""
		from otto.otto.doctype.otto_tool.otto_tool import execute_tool

		# Create external tool
		tool = OttoTool.new(
			title="Multiply Numbers External",
			slug="multiply_numbers_external",
			description="Multiplies two numbers using external function",
			is_external=True,
			args=[
				{
					"arg_name": "x",
					"type": "number",
					"description": "First number",
					"is_required": True,
				},
				{
					"arg_name": "y",
					"type": "number",
					"description": "Second number",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(tool)

		# Define multiplication function
		def multiply_fn(x: int, y: int):
			return x * y

		# Execute using execute_tool
		assert tool.name is not None
		update = execute_tool(
			tool=tool.name,
			args={"x": 7, "y": 3},
			tool_use_id="test_tool_use_123",
			env_str=None,
			permission_granted=True,
			fn=multiply_fn,
		)

		# Verify ToolUseUpdate structure
		self.assertEqual(update.get("id"), "test_tool_use_123")
		self.assertFalse(update.get("is_error"))
		self.assertEqual(update.get("result"), 21)
		self.assertEqual(update.get("stdout"), "")
		self.assertEqual(update.get("stderr"), "")
		self.assertIsNotNone(update.get("start_time"))
		self.assertIsNotNone(update.get("end_time"))

	def test_external_tool_execution_with_dict_return(self):
		"""Test external tool that returns a dictionary."""
		tool = OttoTool.new(
			title="Process Data External",
			slug="process_data_external",
			description="Processes data and returns a dictionary",
			is_external=True,
			args=[
				{
					"arg_name": "name",
					"type": "string",
					"description": "Name to process",
					"is_required": True,
				},
				{
					"arg_name": "age",
					"type": "integer",
					"description": "Age to process",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(tool)

		# Function that returns a dictionary
		def process_fn(name: str, age: int):
			return {
				"greeting": f"Hello, {name}!",
				"age_in_months": age * 12,
				"status": "processed",
			}

		# Execute the tool
		result = tool.execute({"name": "Alice", "age": 25}, fn=process_fn)

		# Verify result
		self.assertIsInstance(result["result"], dict)
		self.assertEqual(result["result"]["greeting"], "Hello, Alice!")
		self.assertEqual(result["result"]["age_in_months"], 300)
		self.assertEqual(result["result"]["status"], "processed")

	def test_external_tool_execution_permission_denied(self):
		"""Test execute_tool with permission denied."""
		from otto.otto.doctype.otto_tool.otto_tool import execute_tool

		# Create external tool
		tool = OttoTool.new(
			title="Sensitive Operation",
			slug="sensitive_operation",
			description="A sensitive operation that requires permission",
			is_external=True,
			args=[
				{
					"arg_name": "data",
					"type": "string",
					"description": "Data to process",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(tool)

		def dummy_fn():
			return "should not execute"

		# Execute with permission denied
		assert tool.name is not None
		update = execute_tool(
			tool=tool.name,
			args={"data": "test"},
			tool_use_id="test_denied_456",
			env_str=None,
			permission_granted=False,
			denied_reason="User denied permission",
			fn=dummy_fn,
		)

		# Verify permission denial
		self.assertEqual(update.get("id"), "test_denied_456")
		self.assertTrue(update.get("is_error"))
		self.assertEqual(update.get("result"), "User denied permission")

	def test_external_tool_execution_without_function_fails(self):
		"""Test that executing external tool without function raises error."""
		tool = OttoTool.new(
			title="External Without Function",
			slug="external_without_function",
			description="External tool without function",
			is_external=True,
			args=[
				{
					"arg_name": "param",
					"type": "string",
					"description": "A parameter",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(tool)

		# Attempting to execute without fn should raise ValidationError
		with self.assertRaises(ValidationError) as context:
			tool.execute({"param": "test"})

		self.assertIn("External tools must be executed with a function", str(context.exception))

	def test_external_tool_with_optional_args(self):
		"""Test external tool with optional arguments."""
		tool = OttoTool.new(
			title="Format String External",
			slug="format_string_external",
			description="Formats a string with optional parameters",
			is_external=True,
			args=[
				{
					"arg_name": "text",
					"type": "string",
					"description": "Text to format",
					"is_required": True,
				},
				{
					"arg_name": "uppercase",
					"type": "boolean",
					"description": "Whether to convert to uppercase",
					"is_required": False,
				},
				{
					"arg_name": "prefix",
					"type": "string",
					"description": "Prefix to add",
					"is_required": False,
				},
			],
		)
		self.created_tools.append(tool)

		def format_fn(text: str, uppercase: bool = False, prefix: str | None = None):
			if uppercase:
				text = text.upper()
			if prefix:
				text = f"{prefix}: {text}"
			return text

		# Test with only required arg
		result1 = tool.execute({"text": "hello"}, fn=format_fn)
		self.assertEqual(result1["result"], "hello")

		# Test with uppercase
		result2 = tool.execute({"text": "hello", "uppercase": True}, fn=format_fn)
		self.assertEqual(result2["result"], "HELLO")

		# Test with all args
		result3 = tool.execute({"text": "world", "uppercase": True, "prefix": "Message"}, fn=format_fn)
		self.assertEqual(result3["result"], "Message: WORLD")

	def test_external_tool_file_operation_simulation(self):
		"""Test external tool simulating a file read operation."""
		# Create external tool for reading files
		tool = OttoTool.new(
			title="Read File",
			slug="read_file",
			description="Reads contents from a file",
			is_external=True,
			args=[
				{
					"arg_name": "filepath",
					"type": "string",
					"description": "Path to the file to read",
					"is_required": True,
				},
				{
					"arg_name": "max_lines",
					"type": "integer",
					"description": "Maximum number of lines to read",
					"is_required": False,
				},
			],
		)
		self.created_tools.append(tool)

		# Define the function that would be called by the external system
		def read_file_fn(filepath: str, max_lines: int | None = None):
			# Simulate reading a file
			simulated_content = [
				"Line 1: Hello World",
				"Line 2: This is a test",
				"Line 3: External tools are working",
				"Line 4: End of file",
			]

			if max_lines:
				simulated_content = simulated_content[:max_lines]

			return {
				"filepath": filepath,
				"content": "\n".join(simulated_content),
				"lines_read": len(simulated_content),
			}

		# Execute tool with filepath only
		result1 = tool.execute({"filepath": "/path/to/file.txt"}, fn=read_file_fn)
		self.assertIsInstance(result1["result"], dict)
		self.assertEqual(result1["result"]["filepath"], "/path/to/file.txt")
		self.assertEqual(result1["result"]["lines_read"], 4)
		self.assertIn("Hello World", result1["result"]["content"])

		# Execute tool with max_lines limit
		result2 = tool.execute({"filepath": "/path/to/file.txt", "max_lines": 2}, fn=read_file_fn)
		self.assertEqual(result2["result"]["lines_read"], 2)
		self.assertIn("Line 1", result2["result"]["content"])
		self.assertIn("Line 2", result2["result"]["content"])
		self.assertNotIn("Line 3", result2["result"]["content"])

	def test_external_tool_api_call_simulation(self):
		"""Test external tool simulating an API call with error handling."""
		# Create external tool for making API calls
		tool = OttoTool.new(
			title="Fetch User Data",
			slug="fetch_user_data",
			description="Fetches user data from an external API",
			is_external=True,
			args=[
				{
					"arg_name": "user_id",
					"type": "string",
					"description": "The user ID to fetch data for",
					"is_required": True,
				},
				{
					"arg_name": "include_metadata",
					"type": "boolean",
					"description": "Whether to include metadata in the response",
					"is_required": False,
				},
			],
		)
		self.created_tools.append(tool)

		# Define the function that simulates an API call
		def fetch_user_data_fn(user_id: str, include_metadata: bool = False):
			# Simulate API response based on user_id
			if user_id == "user123":
				response: dict = {
					"user_id": user_id,
					"name": "John Doe",
					"email": "john@example.com",
					"status": "active",
				}

				if include_metadata:
					response["metadata"] = {
						"created_at": "2024-01-01",
						"last_login": "2025-10-24",
						"account_type": "premium",
					}

				return response

			# Simulate user not found
			return {
				"error": "User not found",
				"user_id": user_id,
			}

		# Execute tool for existing user without metadata
		result1 = tool.execute({"user_id": "user123"}, fn=fetch_user_data_fn)
		self.assertIsInstance(result1["result"], dict)
		self.assertEqual(result1["result"]["user_id"], "user123")
		self.assertEqual(result1["result"]["name"], "John Doe")
		self.assertEqual(result1["result"]["email"], "john@example.com")
		self.assertNotIn("metadata", result1["result"])

		# Execute tool with metadata included
		result2 = tool.execute({"user_id": "user123", "include_metadata": True}, fn=fetch_user_data_fn)
		self.assertIn("metadata", result2["result"])
		self.assertEqual(result2["result"]["metadata"]["account_type"], "premium")

		# Execute tool for non-existent user
		result3 = tool.execute({"user_id": "nonexistent"}, fn=fetch_user_data_fn)
		self.assertIn("error", result3["result"])
		self.assertEqual(result3["result"]["error"], "User not found")

	def test_external_tool_with_import_path(self):
		"""Test external tool that uses tool_import_path instead of passing fn parameter."""
		# Create external tool with tool_import_path
		tool = OttoTool.new(
			title="Calculate With Import",
			slug="calculate_with_import",
			description="Calculates sum and product using imported function",
			args=[
				{
					"arg_name": "x",
					"type": "integer",
					"description": "First number",
					"is_required": True,
				},
				{
					"arg_name": "y",
					"type": "integer",
					"description": "Second number",
					"is_required": True,
				},
			],
			is_app_defined=True,
			tool_import_path="otto.otto.doctype.otto_tool.test_otto_tool.test_import_function",
		)
		self.created_tools.append(tool)

		# Execute without passing fn - it should import the function automatically
		result = tool.execute({"x": 6, "y": 7})

		# Verify result from the imported function
		self.assertIsInstance(result["result"], dict)
		self.assertEqual(result["result"]["sum"], 13)
		self.assertEqual(result["result"]["product"], 42)
		self.assertEqual(result["stdout"], "")
		self.assertEqual(result["stderr"], "")
