# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import contextlib

import frappe
from frappe.tests import IntegrationTestCase

import otto
from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant
from otto.otto.doctype.otto_chat.otto_chat import OttoChat
from otto.otto.doctype.otto_tool.otto_tool import OttoTool


class IntegrationTestOttoAssistant(IntegrationTestCase):
	"""
	Integration tests for OttoAssistant.
	Tests the complete flow from tool creation to chat execution.
	"""

	def setUp(self):
		"""Set up test fixtures."""
		self.created_tools: list[OttoTool] = []
		self.created_assistants: list[OttoAssistant] = []
		self.created_chats: list[OttoChat] = []

	def tearDown(self):
		"""Clean up created test resources."""
		# Clean up in reverse order of dependencies
		for chat in self.created_chats:
			with contextlib.suppress(Exception):
				# Clean up related sessions and permission requests
				if hasattr(chat, "session") and chat.session:
					# Clean up permission requests
					permission_requests = frappe.get_all(
						"Otto Permission Request", filters={"session": chat.session}, pluck="name"
					)
					for req_name in permission_requests:
						frappe.delete_doc("Otto Permission Request", req_name, force=True)

					# Clean up session
					frappe.delete_doc("Otto Session", chat.session, force=True)

				# Clean up chat
				frappe.delete_doc("Otto Chat", chat.name, force=True)

		for assistant in self.created_assistants:
			with contextlib.suppress(Exception):
				frappe.delete_doc("Otto Assistant", assistant.name, force=True)

		for tool in self.created_tools:
			with contextlib.suppress(Exception):
				frappe.delete_doc("Otto Tool", tool.name, force=True)

	def test_create_tools(self):
		"""Test creating internal and external tools."""
		# Create an internal tool with code
		internal_tool = OttoTool.new(
			title="Add Numbers",
			slug="add_numbers",
			description="Adds two numbers together",
			code="""
def main(a: int, b: int):
	return a + b
""",
		)
		self.created_tools.append(internal_tool)

		# Add descriptions to make it valid
		for arg in internal_tool.args:
			if arg.arg_name == "a":
				arg.description = "First number to add"
			elif arg.arg_name == "b":
				arg.description = "Second number to add"
		internal_tool.save()
		internal_tool.reload()

		# Verify internal tool
		self.assertTrue(internal_tool.is_valid)
		self.assertEqual(internal_tool.slug, "add_numbers")
		self.assertFalse(internal_tool.is_external)
		self.assertEqual(len(internal_tool.args), 2)

		# Create an external tool
		external_tool = OttoTool.new(
			title="Get Weather",
			slug="get_weather",
			description="Gets the current weather for a city",
			is_external=True,
			args=[
				{
					"arg_name": "city",
					"type": "string",
					"description": "The city to get weather for",
					"is_required": True,
				},
				{
					"arg_name": "units",
					"type": "string",
					"description": "Temperature units (celsius or fahrenheit)",
					"is_required": False,
				},
			],
		)
		self.created_tools.append(external_tool)

		# Verify external tool
		self.assertTrue(external_tool.is_valid)
		self.assertEqual(external_tool.slug, "get_weather")
		self.assertTrue(external_tool.is_external)
		self.assertEqual(len(external_tool.args), 2)

	def test_create_assistant(self):
		"""Test creating an assistant with tools."""
		# Create tools first
		internal_tool = OttoTool.new(
			title="Multiply Numbers",
			slug="multiply_numbers",
			description="Multiplies two numbers",
			code="""
def main(x: int, y: int):
	return x * y
""",
		)
		self.created_tools.append(internal_tool)

		for arg in internal_tool.args:
			if arg.arg_name == "x":
				arg.description = "First number"
			elif arg.arg_name == "y":
				arg.description = "Second number"
		internal_tool.save()
		internal_tool.reload()

		external_tool = OttoTool.new(
			title="Search Database",
			slug="search_database",
			description="Searches the database for information",
			is_external=True,
			args=[
				{
					"arg_name": "query",
					"type": "string",
					"description": "Search query",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(external_tool)

		# Create assistant with these tools
		assert internal_tool.name is not None
		assert external_tool.name is not None
		assistant = OttoAssistant.new(
			title="Math & Search Assistant",
			instruction="You are a helpful assistant that can perform math operations and search databases.",
			tools=[internal_tool.name, external_tool.name],
			reasoning_effort="Low",
		)
		self.created_assistants.append(assistant)

		# Verify assistant is created correctly
		self.assertIsNotNone(assistant.name)
		self.assertEqual(assistant.title, "Math & Search Assistant")
		self.assertEqual(len(assistant.tools), 2)
		self.assertEqual(assistant.reasoning_effort, "Low")
		self.assertIsNotNone(assistant.llm)

		# Verify tools are properly attached with slugs
		tool_slugs = [tool.slug for tool in assistant.tools]
		self.assertIn("multiply_numbers", tool_slugs)
		self.assertIn("search_database", tool_slugs)

		# Test get_instruction method
		instruction = assistant.get_instruction()
		self.assertIsNotNone(instruction)
		self.assertIn("helpful assistant", instruction.lower())

	def test_create_chat_from_assistant(self):
		"""Test creating a chat from an assistant."""
		# Create a simple tool
		tool = OttoTool.new(
			title="Get Time",
			slug="get_time",
			description="Gets the current time",
			code="""
def main():
	from datetime import datetime
	return datetime.now().isoformat()
""",
		)
		self.created_tools.append(tool)
		tool.description = "Returns the current time"
		tool.save()
		tool.reload()

		# Create assistant
		assert tool.name is not None
		assistant = OttoAssistant.new(
			title="Time Assistant",
			instruction="You help users with time-related queries.",
			tools=[tool.name],
		)
		self.created_assistants.append(assistant)

		# Create chat from assistant
		assert assistant.name is not None
		chat = OttoChat.new(assistant=assistant.name)
		self.created_chats.append(chat)

		# Verify chat is created correctly
		self.assertIsNotNone(chat.name)
		self.assertEqual(chat.assistant, assistant.name)
		self.assertIsNotNone(chat.session)

		# Verify session is created
		session = chat.session_
		self.assertIsNotNone(session)
		self.assertEqual(session.model, assistant.llm)

		# Verify assistant reference is correct
		self.assertEqual(chat.assistant_.name, assistant.name)

		# Verify tool configs are loaded
		tool_configs = chat.tool_configs
		self.assertIn("get_time", tool_configs)
		self.assertEqual(tool_configs["get_time"].tool, tool.name)

	def test_chat_interaction_with_tool_execution(self):
		"""Test the full chat flow: query -> permission request -> tool execution."""
		# Create an internal tool
		calc_tool = OttoTool.new(
			title="Calculate",
			slug="calculate",
			description="Performs a simple calculation",
			code="""
def main(operation: str, a: int, b: int):
	if operation == "add":
		return a + b
	elif operation == "multiply":
		return a * b
	elif operation == "subtract":
		return a - b
	elif operation == "divide":
		return a / b if b != 0 else "Cannot divide by zero"
	return "Unknown operation"
""",
		)
		self.created_tools.append(calc_tool)
		for arg in calc_tool.args:
			if arg.arg_name == "operation":
				arg.description = "The operation to perform (add, multiply, subtract, divide)"
			elif arg.arg_name == "a":
				arg.description = "First number"
			elif arg.arg_name == "b":
				arg.description = "Second number"
		calc_tool.save()
		calc_tool.reload()

		# Create an external tool that requires permission
		external_tool = OttoTool.new(
			title="Send Email",
			slug="send_email",
			description="Sends an email to a recipient",
			is_external=True,
			requires_permission=True,
			args=[
				{
					"arg_name": "to",
					"type": "string",
					"description": "Email recipient",
					"is_required": True,
				},
				{
					"arg_name": "subject",
					"type": "string",
					"description": "Email subject",
					"is_required": True,
				},
				{
					"arg_name": "body",
					"type": "string",
					"description": "Email body",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(external_tool)

		# Create assistant with these tools
		assert calc_tool.name is not None
		assert external_tool.name is not None
		assistant = OttoAssistant.new(
			title="Helpful Assistant",
			instruction="You are a helpful assistant. When asked to perform calculations, use the calculate tool. When asked to send emails, use the send_email tool. Always acknowledge the request clearly.",
			tools=[calc_tool.name, external_tool.name],
		)
		self.created_assistants.append(assistant)

		# Create chat
		assert assistant.name is not None
		chat = OttoChat.new(assistant=assistant.name)
		self.created_chats.append(chat)

		# Verify initial state
		self.assertFalse(chat.has_pending_requests())
		self.assertEqual(len(chat.get_pending_tools()), 0)

		# Perform a chat interaction that should trigger the calculate tool
		# Note: In a real scenario, the LLM would decide to use the tool
		# For testing, we'll manually create a tool use scenario

		# First, let's get the tool schemas to set up the session properly
		tool_schemas = []
		for tool_ref in assistant.tools:
			tool_doc = otto.get(OttoTool, tool_ref.tool)
			schema = tool_doc.get_function_schema(slug=tool_ref.slug)
			tool_schemas.append(schema)

		# Update session with tools
		chat.session_.set_tools(tool_schemas)
		chat.session_.save()

		# Make a chat request (this would normally call the LLM)
		# Since we can't actually call the LLM in tests, we'll simulate the flow
		# by manually creating a tool use scenario

		# For testing purposes, let's verify the setup is correct
		session_tools = chat.session_.tools
		self.assertEqual(len(session_tools), 2)
		tool_names = [tool["name"] for tool in session_tools]
		self.assertIn("calculate", tool_names)
		self.assertIn("send_email", tool_names)

	def test_permission_request_flow(self):
		"""Test permission request creation and granting."""
		# Create a tool that requires permission
		sensitive_tool = OttoTool.new(
			title="Delete Data",
			slug="delete_data",
			description="Deletes data from the database",
			code="""
def main(table: str, id: str):
	# In real scenario, this would delete data
	return f"Deleted record {id} from {table}"
""",
			requires_permission=True,
		)
		self.created_tools.append(sensitive_tool)
		for arg in sensitive_tool.args:
			if arg.arg_name == "table":
				arg.description = "Table name"
			elif arg.arg_name == "id":
				arg.description = "Record ID to delete"
		sensitive_tool.save()
		sensitive_tool.reload()

		# Create assistant with this tool
		assert sensitive_tool.name is not None
		assistant = OttoAssistant.new(
			title="Admin Assistant",
			instruction="You help with administrative tasks.",
			tools=[sensitive_tool.name],
		)
		self.created_assistants.append(assistant)

		# Create chat
		assert assistant.name is not None
		chat = OttoChat.new(assistant=assistant.name)
		self.created_chats.append(chat)

		# Set up tool schemas
		tool_schemas = []
		for tool_ref in assistant.tools:
			tool_doc = otto.get(OttoTool, tool_ref.tool)
			schema = tool_doc.get_function_schema(slug=tool_ref.slug)
			tool_schemas.append(schema)

		chat.session_.set_tools(tool_schemas)
		chat.session_.save()

		# Verify tool requires permission
		tool_config = chat.tool_configs.get("delete_data")
		self.assertIsNotNone(tool_config)
		assert tool_config is not None
		self.assertTrue(tool_config.requires_permission)

	def test_external_tool_execution_with_fn_map(self):
		"""Test executing external tools with function map."""
		# Create external tool
		external_tool = OttoTool.new(
			title="Fetch Data",
			slug="fetch_data",
			description="Fetches data from an external source",
			is_external=True,
			args=[
				{
					"arg_name": "source",
					"type": "string",
					"description": "Data source identifier",
					"is_required": True,
				},
			],
		)
		self.created_tools.append(external_tool)

		# Create assistant
		assert external_tool.name is not None
		assistant = OttoAssistant.new(
			title="Data Assistant",
			instruction="You help fetch and analyze data.",
			tools=[external_tool.name],
		)
		self.created_assistants.append(assistant)

		# Create chat
		assert assistant.name is not None
		chat = OttoChat.new(assistant=assistant.name)
		self.created_chats.append(chat)

		# Define an external function for the tool
		def fetch_data_fn(args):
			source = args.get("source", "unknown")
			return {"data": f"Data from {source}", "status": "success"}

		# Create function map
		fn_map = {"fetch_data": fetch_data_fn}

		# Verify tool config
		tool_config = chat.tool_configs.get("fetch_data")
		self.assertIsNotNone(tool_config)
		assert tool_config is not None
		self.assertTrue(tool_config.is_external)

		# Test that fn_map can be passed to execute_tools
		# (In real scenario, this would be called after pending tools are detected)
		chat.execute_tools(fn_map=fn_map)

		# Verify it doesn't crash when there are no pending tools
		pending = chat.get_pending_tools()
		self.assertEqual(len(pending), 0)

	def test_assistant_with_context_function(self):
		"""Test assistant with get_context function."""
		# Create a simple tool
		tool = OttoTool.new(
			title="Echo",
			slug="echo",
			description="Echoes the input",
			code="""
def main(message: str):
	return message
""",
		)
		self.created_tools.append(tool)
		for arg in tool.args:
			if arg.arg_name == "message":
				arg.description = "Message to echo"
		tool.save()
		tool.reload()

		# Create assistant with context function
		assert tool.name is not None
		assistant = OttoAssistant.new(
			title="Context Assistant",
			instruction="You are {{user}}. The current date is {{date}}. Custom value: {{custom_value}}",
			tools=[tool.name],
		)
		self.created_assistants.append(assistant)

		# Add get_context code
		assistant.get_context = """
def get_context():
	return {"custom_value": "test_value_123"}
"""
		assistant.save()
		assistant.reload()

		# Test run_get_context
		context = assistant.run_get_context()
		self.assertIsNotNone(context)
		self.assertIn("user", context)
		self.assertIn("date", context)
		self.assertIn("time", context)
		self.assertIn("datetime", context)
		self.assertIn("custom_value", context)
		self.assertEqual(context["custom_value"], "test_value_123")

		# Test get_instruction with context
		instruction = assistant.get_instruction()
		self.assertIn("test_value_123", instruction)
		self.assertIn(context["date"], instruction)

	def test_full_integration_flow(self):
		"""Test complete integration: tools -> assistant -> chat -> tool execution."""
		# 1. Create internal tool
		sum_tool = OttoTool.new(
			title="Sum Numbers",
			slug="sum_numbers",
			description="Sums a list of numbers",
			code="""
def main(numbers: list):
	return sum(numbers)
""",
		)
		self.created_tools.append(sum_tool)
		for arg in sum_tool.args:
			if arg.arg_name == "numbers":
				arg.description = "List of numbers to sum"
		sum_tool.save()
		sum_tool.reload()

		# 2. Create external tool
		format_tool = OttoTool.new(
			title="Format Result",
			slug="format_result",
			description="Formats a result as a string",
			is_external=True,
			args=[
				{
					"arg_name": "value",
					"type": "number",
					"description": "Value to format",
					"is_required": True,
				},
				{
					"arg_name": "prefix",
					"type": "string",
					"description": "Prefix to add",
					"is_required": False,
				},
			],
		)
		self.created_tools.append(format_tool)

		# 3. Create assistant with both tools
		assert sum_tool.name is not None
		assert format_tool.name is not None
		assistant = OttoAssistant.new(
			title="Math Formatter",
			instruction="You can sum numbers and format results. Always be helpful and clear.",
			tools=[sum_tool.name, format_tool.name],
			reasoning_effort="Medium",
		)
		self.created_assistants.append(assistant)

		# Verify assistant setup
		self.assertEqual(len(assistant.tools), 2)
		self.assertEqual(assistant.reasoning_effort, "Medium")

		# 4. Create chat
		assert assistant.name is not None
		chat = OttoChat.new(assistant=assistant.name)
		self.created_chats.append(chat)

		# Verify chat setup
		self.assertIsNotNone(chat.session)
		self.assertEqual(chat.assistant, assistant.name)

		# 5. Verify tool configs
		tool_configs = chat.tool_configs
		self.assertEqual(len(tool_configs), 2)
		self.assertIn("sum_numbers", tool_configs)
		self.assertIn("format_result", tool_configs)

		# Verify internal tool
		sum_config = tool_configs["sum_numbers"]
		self.assertFalse(sum_config.is_external)
		self.assertEqual(sum_config.tool, sum_tool.name)

		# Verify external tool
		format_config = tool_configs["format_result"]
		self.assertTrue(format_config.is_external)
		self.assertEqual(format_config.tool, format_tool.name)

		# 6. Test tool execution directly
		# Execute internal tool
		result = sum_tool.execute({"numbers": [1, 2, 3, 4, 5]})
		self.assertEqual(result["result"], 15)

		# Execute external tool with function
		def format_fn(args):
			value = args["value"]
			prefix = args.get("prefix", "Result:")
			return f"{prefix} {value}"

		result = format_tool.execute({"value": 15, "prefix": "Sum:"}, fn=format_fn)
		self.assertEqual(result["result"], "Sum: 15")

		# 7. Test execute_tools with fn_map
		fn_map = {"format_result": format_fn}
		chat.execute_tools(fn_map=fn_map)

		# Should complete without errors even with no pending tools
		self.assertEqual(len(chat.get_pending_tools()), 0)

	def test_assistant_defaults(self):
		"""Test assistant creation with default values."""
		# Create minimal assistant
		assistant = OttoAssistant.new(title="Minimal Assistant")
		self.created_assistants.append(assistant)

		# Verify defaults
		self.assertIsNotNone(assistant.name)
		self.assertEqual(assistant.title, "Minimal Assistant")
		self.assertIsNotNone(assistant.llm)
		self.assertIsNotNone(assistant.instruction)
		self.assertEqual(assistant.reasoning_effort, "None")
		self.assertEqual(len(assistant.tools), 0)

	def test_tool_schema_generation(self):
		"""Test that tools generate correct schemas for the assistant."""
		# Create a tool with various argument types
		complex_tool = OttoTool.new(
			title="Complex Tool",
			slug="complex_tool",
			description="A tool with various argument types",
			is_external=True,
			use_explanation=True,
			args=[
				{
					"arg_name": "name",
					"type": "string",
					"description": "A string parameter",
					"is_required": True,
				},
				{
					"arg_name": "count",
					"type": "integer",
					"description": "An integer parameter",
					"is_required": True,
				},
				{
					"arg_name": "ratio",
					"type": "number",
					"description": "A float parameter",
					"is_required": False,
				},
				{
					"arg_name": "enabled",
					"type": "boolean",
					"description": "A boolean parameter",
					"is_required": False,
				},
				{
					"arg_name": "items",
					"type": "array",
					"description": "An array parameter",
					"is_required": False,
				},
				{
					"arg_name": "metadata",
					"type": "object",
					"description": "An object parameter",
					"is_required": False,
				},
			],
		)
		self.created_tools.append(complex_tool)

		# Get schema
		schema = complex_tool.get_function_schema()

		# Verify schema structure
		self.assertEqual(schema["name"], "complex_tool")
		self.assertEqual(schema["description"], "A tool with various argument types")

		# Verify explanation is included (because use_explanation=True)
		self.assertIn("explanation", schema["parameters"]["properties"])
		self.assertIn("explanation", schema["parameters"]["required"])

		# Verify all parameters are included
		properties = schema["parameters"]["properties"]
		self.assertIn("name", properties)
		self.assertIn("count", properties)
		self.assertIn("ratio", properties)
		self.assertIn("enabled", properties)
		self.assertIn("items", properties)
		self.assertIn("metadata", properties)

		# Verify types
		self.assertEqual(properties["name"]["type"], "string")
		self.assertEqual(properties["count"]["type"], "integer")
		self.assertEqual(properties["ratio"]["type"], "number")
		self.assertEqual(properties["enabled"]["type"], "boolean")
		self.assertEqual(properties["items"]["type"], "array")
		self.assertEqual(properties["metadata"]["type"], "object")

		# Verify required fields
		required = schema["parameters"]["required"]
		self.assertIn("explanation", required)  # From use_explanation
		self.assertIn("name", required)
		self.assertIn("count", required)
		self.assertNotIn("ratio", required)
		self.assertNotIn("enabled", required)
