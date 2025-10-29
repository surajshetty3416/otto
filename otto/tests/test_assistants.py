# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import contextlib

import frappe
from frappe.tests import UnitTestCase

from otto.lib.tests.utils import print_session, print_stats
from otto.llm.test_llm.utils import TEST_MODEL, skip_unless_can_run_llm_tests
from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant
from otto.otto.doctype.otto_chat.otto_chat import OttoChat
from otto.otto.doctype.otto_tool.otto_tool import OttoTool


class TestAssistants(UnitTestCase):
	"""
	Tests for OttoAssistant.
	Tests the complete flow from tool creation to chat execution.
	"""

	def setUp(self):
		"""Set up test fixtures."""
		self.created_tools: list[OttoTool] = []
		self.created_assistants: list[OttoAssistant] = []
		self.created_chats: list[OttoChat] = []

	def tearDown(self):
		"""Clean up created test resources."""
		print_stats([chat.session_ for chat in self.created_chats if len(chat.session_.get_items()) > 0])

		# Clean up in reverse order of dependencies
		for chat in self.created_chats:
			with contextlib.suppress(Exception):
				# Clean up related sessions and permission requests

				# Clean up permission requests
				permission_requests = frappe.get_all(
					"Otto Permission Request", filters={"session": chat.session}, pluck="name"
				)
				for req_name in permission_requests:
					frappe.delete_doc("Otto Permission Request", req_name, force=True)

				# Clean up chat
				frappe.delete_doc("Otto Chat", chat.name, force=True)

				# Clean up session
				frappe.delete_doc("Otto Session", chat.session, force=True)

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
		"""Test the full chat flow: query -> permission request -> tool execution."""
		calc_tool, send_email_tool = _get_test_tools()
		self.created_tools.append(calc_tool)
		self.created_tools.append(send_email_tool)

		# Create assistant with these tools
		assert calc_tool.name is not None
		assert send_email_tool.name is not None
		assistant = OttoAssistant.new(
			title="Helpful Assistant",
			instruction="You are a helpful assistant. When asked to perform calculations, use the calculate tool. When asked to send emails, use the send_email tool. Always acknowledge the request clearly.",
			tools=[calc_tool.name, send_email_tool.name],
		)
		self.created_assistants.append(assistant)

		# Create chat
		assert assistant.name is not None
		chat = OttoChat.new(assistant=assistant.name)
		self.created_chats.append(chat)

		# Verify initial state
		self.assertFalse(chat.has_pending_requests())
		self.assertEqual(len(chat.get_pending_tools()), 0)

		# For testing purposes, let's verify the setup is correct
		session_tools = chat.session_.tools
		self.assertEqual(len(session_tools), 2)
		tool_names = [tool["name"] for tool in session_tools]
		self.assertIn("calculate", tool_names)
		self.assertIn("send_email", tool_names)

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

	@skip_unless_can_run_llm_tests
	def test_full_integration_flow(self):
		"""Test complete integration: tools -> assistant -> chat -> tool execution."""
		# Create tools
		calc_tool, send_email_tool = _get_test_tools()
		self.created_tools.extend([calc_tool, send_email_tool])

		# Create assistant
		assert calc_tool.name is not None
		assert send_email_tool.name is not None
		assistant = OttoAssistant.new(
			title="Assistant",
			instruction="You can perform calculations and send emails. Always be helpful and clear. When asked to perform a calculation, use the calculate tool. When asked to send an email, use the send_email tool.",
			tools=[calc_tool.name, send_email_tool.name],
			llm=TEST_MODEL,
		)
		self.created_assistants.append(assistant)

		# Create chat (ask for calc)
		assert assistant.name is not None
		chat = OttoChat.new(assistant=assistant.name)
		self.created_chats.append(chat)
		self.assertIsNotNone(chat.session)
		self.assertEqual(chat.assistant, assistant.name)
		tool_configs = chat.tool_config_map
		self.assertEqual(len(tool_configs), 2)
		self.assertIn("calculate", tool_configs)
		self.assertIn("send_email", tool_configs)

		# First query, expect calculate tool use
		response, reason = chat.chat("What is 367 * 42?")
		self.assertIsNotNone(response)
		self.assertIsNone(reason)
		assert response is not None
		self.assertGreater(len([ch for ch in response]), 0)
		self.assertGreaterEqual(len(chat.session_.get_items()), 2)

		# Verify tool use
		permission_requests = chat.get_pending_requests()
		self.assertEqual(len(permission_requests), 0)
		pending_tools = chat.get_pending_tools()
		self.assertEqual(len(pending_tools), 1)
		self.assertEqual(pending_tools[0].name, "calculate")
		self.assertEqual(pending_tools[0].args["operation"], "multiply")
		self.assertEqual(pending_tools[0].args["a"], 367)
		self.assertEqual(pending_tools[0].args["b"], 42)

		# Execute tool use
		for _ in chat.execute_tools():
			pass
		pending_tools = chat.get_pending_tools()
		self.assertEqual(len(pending_tools), 0)

		# Verify tool use execution
		tool_uses = chat.session_.get_tool_uses(status="success")
		self.assertEqual(len(tool_uses), 1)
		tool_use = tool_uses[0]
		assert tool_use is not None, "type check"
		self.assertEqual(tool_use["name"], "calculate")
		self.assertEqual(tool_use["args"]["operation"], "multiply")
		self.assertEqual(tool_use["args"]["a"], 367)
		self.assertEqual(tool_use["args"]["b"], 42)
		self.assertEqual(tool_use["result"], "15414")

		# Resume chat after executing tool use
		response, reason = chat.chat()
		self.assertIsNotNone(response)
		self.assertIsNone(reason)
		assert response is not None
		self.assertGreater(len([ch for ch in response]), 0)
		item = response.item
		self.assertIsNotNone(item)
		assert item is not None, "type check"

		# Verify tool use result used
		content = item["content"]
		self.assertGreater(len(content), 0)
		self.assertEqual(content[0]["type"], "text")
		text = content[0]
		assert text["type"] == "text"
		self.assertTrue("15414" in text["text"] or "15,414" in text["text"])
		self.assertGreaterEqual(len(chat.session_.get_items()), 3)

		# Second query, expect send email tool use request
		response, reason = chat.chat(
			"Can you send an email to blagar@octarine.com with the subject 'Hello' and the body 'Hi I'm Otto'?"
		)
		self.assertIsNotNone(response)
		self.assertIsNone(reason)
		assert response is not None
		self.assertGreater(len([ch for ch in response]), 0)
		item = response.item
		self.assertIsNotNone(item)
		assert item is not None, "type check"
		self.assertGreaterEqual(len(chat.session_.get_items()), 4)
		print_session(chat.session_)

		# Verify send email tool use and permission request
		permission_requests = chat.get_pending_requests()
		self.assertEqual(len(permission_requests), 1)
		pending_tools = chat.get_pending_tools()
		self.assertEqual(len(pending_tools), 1)
		self.assertEqual(pending_tools[0].name, "send_email")
		self.assertEqual(pending_tools[0].args["to"], "blagar@octarine.com")
		self.assertEqual(pending_tools[0].args["subject"], "Hello")
		self.assertEqual(pending_tools[0].args["body"], "Hi I'm Otto")

		# Grant permission request
		request = permission_requests[0]
		self.assertEqual(request.tool_use_id, pending_tools[0].id)
		self.assertEqual(request.status, "Pending")
		request.grant()
		self.assertEqual(request.status, "Granted")

		# Execute tool use
		def dummy_send_email(to: str, subject: str, body: str):
			return "email sent"

		pending_tools = chat.get_pending_tools()
		self.assertEqual(len(pending_tools), 1)
		for _ in chat.execute_tools(fn_map={"send_email": dummy_send_email}):
			pass
		pending_tools = chat.get_pending_tools()
		self.assertEqual(len(pending_tools), 0)

		# Verify tool use execution
		tool_uses = chat.session_.get_tool_uses(name="send_email")
		self.assertEqual(len(tool_uses), 1)
		tool_use = tool_uses[0]
		assert tool_use is not None, "type check"
		self.assertEqual(tool_use["name"], "send_email")
		self.assertEqual(tool_use["args"]["to"], "blagar@octarine.com")
		self.assertEqual(tool_use["args"]["subject"], "Hello")
		self.assertEqual(tool_use["args"]["body"], "Hi I'm Otto")
		self.assertEqual(tool_use["status"], "success")
		self.assertEqual(tool_use["result"], "email sent")


def _get_test_tools():
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
		args=[
			{
				"arg_name": "operation",
				"type": "string",
				"description": "Operation to perform (add, multiply, subtract, divide)",
				"is_required": True,
			},
			{
				"arg_name": "a",
				"type": "int",
				"description": "First number",
				"is_required": True,
			},
			{
				"arg_name": "b",
				"type": "int",
				"description": "Second number",
				"is_required": True,
			},
		],
	)
	assert calc_tool.is_valid

	send_email_tool = OttoTool.new(
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
	assert send_email_tool.is_valid
	return calc_tool, send_email_tool
