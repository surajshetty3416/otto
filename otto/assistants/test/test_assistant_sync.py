# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import contextlib

import frappe
from frappe.tests import UnitTestCase

import otto
from otto.assistants import sync_assistants
from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant
from otto.otto.doctype.otto_tool.otto_tool import OttoTool


class TestAssistantSync(UnitTestCase):
	"""
	Tests for assistant synchronization via sync_assistants function.
	Tests that assistants and their tools are correctly created/updated.
	"""

	def setUp(self):
		"""Set up test fixtures."""
		self.created_assistants: list[str] = []
		self.created_tools: list[str] = []

	def tearDown(self):
		"""Clean up created test resources."""
		# Clean up in reverse order of dependencies
		for assistant_name in self.created_assistants:
			with contextlib.suppress(Exception):
				if frappe.db.exists("Otto Assistant", assistant_name):
					frappe.delete_doc("Otto Assistant", assistant_name, force=True)

		for tool_name in self.created_tools:
			with contextlib.suppress(Exception):
				if frappe.db.exists("Otto Tool", tool_name):
					frappe.delete_doc("Otto Tool", tool_name, force=True)

	def test_sync_assistant_creates_new_assistant(self):
		"""Test that sync_assistants creates a new assistant with tools."""
		from otto.assistants.test import dummy_assistant

		# Sync the dummy assistant
		sync_assistants([dummy_assistant])

		# Track for cleanup
		self.created_assistants.append("test-dummy-assistant")
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Verify assistant was created
		self.assertTrue(frappe.db.exists("Otto Assistant", dummy_assistant.uid))

		# Load and verify assistant
		assistant = otto.get(OttoAssistant, dummy_assistant.uid)
		self.assertEqual(assistant.title, dummy_assistant.name)
		self.assertEqual(assistant.instruction, dummy_assistant.instruction)
		self.assertTrue(assistant.is_app_defined)

		# Verify tools were created and attached
		self.assertEqual(len(assistant.tools), len(dummy_assistant.tools))
		tool_slugs = {tool.slug for tool in assistant.tools}
		self.assertIn("add_numbers", tool_slugs)
		self.assertIn("echo_message", tool_slugs)

		# Verify tools exist in database
		self.assertTrue(frappe.db.exists("Otto Tool", "test-dummy-assistant-add"))
		self.assertTrue(frappe.db.exists("Otto Tool", "test-dummy-assistant-echo"))

		# Verify add tool
		add_tool: OttoTool = otto.get(OttoTool, "test-dummy-assistant-add")
		self.assertEqual(add_tool.title, "Add Numbers")
		self.assertEqual(add_tool.slug, "add_numbers")
		self.assertTrue(add_tool.is_valid)
		self.assertTrue(add_tool.is_app_defined)
		self.assertFalse(add_tool.requires_permission)
		self.assertEqual(len(add_tool.args), 2)

		# Verify echo tool
		echo_tool: OttoTool = otto.get(OttoTool, "test-dummy-assistant-echo")
		self.assertEqual(echo_tool.title, "Echo Message")
		self.assertEqual(echo_tool.slug, "echo_message")
		self.assertTrue(echo_tool.is_valid)
		self.assertTrue(echo_tool.is_app_defined)
		self.assertTrue(echo_tool.requires_permission)
		self.assertEqual(len(echo_tool.args), 1)

	def test_sync_assistant_updates_existing_assistant(self):
		"""Test that sync_assistants updates an existing assistant."""
		from otto.assistants.test import dummy_assistant

		# First sync
		sync_assistants([dummy_assistant])
		self.created_assistants.append(dummy_assistant.uid)
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Modify the assistant
		assistant = otto.get(OttoAssistant, dummy_assistant.uid)
		assistant.title = "Modified Title"
		assistant.save()

		# Sync again
		sync_assistants([dummy_assistant])

		# Verify assistant was updated back to original
		assistant.reload()
		self.assertEqual(assistant.title, "Test Dummy Assistant")
		self.assertTrue(assistant.is_app_defined)

	def test_sync_assistant_with_string_path(self):
		"""Test that sync_assistants works with string module path."""
		from otto.assistants.test import dummy_assistant

		# Sync using string path
		sync_assistants(["otto.assistants.test.dummy_assistant"])

		# Track for cleanup
		self.created_assistants.append(dummy_assistant.uid)
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Verify assistant was created
		self.assertTrue(frappe.db.exists("Otto Assistant", dummy_assistant.uid))
		assistant = otto.get(OttoAssistant, dummy_assistant.uid)
		self.assertEqual(assistant.title, dummy_assistant.name)

	def test_sync_assistant_tools_updated(self):
		"""Test that tools are properly updated when syncing."""
		from otto.assistants.test import dummy_assistant

		# First sync
		sync_assistants([dummy_assistant])
		self.created_assistants.append(dummy_assistant.uid)
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Modify a tool
		add_tool = otto.get(OttoTool, "test-dummy-assistant-add")
		add_tool.title = "Modified Add Tool"
		add_tool.save()

		# Sync again
		sync_assistants([dummy_assistant])

		# Verify tool was updated back
		add_tool.reload()
		self.assertEqual(add_tool.title, "Add Numbers")
		self.assertTrue(add_tool.is_app_defined)

	def test_sync_assistant_with_context_function(self):
		"""Test that assistant with get_context function is properly synced."""
		from otto.assistants.test import dummy_assistant

		# Sync the assistant
		sync_assistants([dummy_assistant])
		self.created_assistants.append(dummy_assistant.uid)
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Load assistant and verify context function
		assistant = otto.get(OttoAssistant, dummy_assistant.uid)
		self.assertIsNotNone(assistant.get_context_import_path)

		# Test running get_context
		context = assistant.run_get_context()
		self.assertIsNotNone(context)
		self.assertIn("test_value", context)
		self.assertEqual(context["test_value"], "dummy_context")

	def test_sync_multiple_assistants(self):
		"""Test syncing multiple assistants at once."""
		from otto.assistants.test import dummy_assistant

		# Create another simple assistant module programmatically for testing
		# We'll just sync the same one twice to verify batch processing works
		sync_assistants([dummy_assistant, "otto.assistants.test.dummy_assistant"])

		# Track for cleanup
		self.created_assistants.append(dummy_assistant.uid)
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Verify assistant exists (synced twice shouldn't cause issues)
		self.assertTrue(frappe.db.exists("Otto Assistant", "test-dummy-assistant"))

	def test_sync_assistant_with_invalid_module_graceful_failure(self):
		"""Test that sync_assistants handles invalid modules gracefully."""
		# This should not raise an exception, just log an error
		sync_assistants(["otto.assistants.test.nonexistent_module"])

		# No cleanup needed since nothing was created

	def test_assistant_tool_import_paths(self):
		"""Test that tool import paths are correctly set."""
		from otto.assistants.test import dummy_assistant

		# Sync the assistant
		sync_assistants([dummy_assistant])
		self.created_assistants.append(dummy_assistant.uid)
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Verify tool import paths
		add_tool = otto.get(OttoTool, "test-dummy-assistant-add")
		self.assertIsNotNone(add_tool.tool_import_path)
		assert add_tool.tool_import_path is not None
		self.assertIn("add_numbers", add_tool.tool_import_path)

		echo_tool: OttoTool = otto.get(OttoTool, "test-dummy-assistant-echo")
		self.assertIsNotNone(echo_tool.tool_import_path)
		assert echo_tool.tool_import_path is not None
		self.assertIn("echo_message", echo_tool.tool_import_path)

	def test_tool_schemas_correctly_synced(self):
		"""Test that tool schemas (args) are correctly synced."""
		from otto.assistants.test import dummy_assistant

		# Sync the assistant
		sync_assistants([dummy_assistant])
		self.created_assistants.append(dummy_assistant.uid)
		self.created_tools.extend(["test-dummy-assistant-add", "test-dummy-assistant-echo"])

		# Verify add_numbers tool schema
		add_tool = otto.get(OttoTool, "test-dummy-assistant-add")
		self.assertEqual(len(add_tool.args), 2)
		arg_names = {arg.arg_name for arg in add_tool.args}
		self.assertIn("a", arg_names)
		self.assertIn("b", arg_names)

		# Check specific arg details
		for arg in add_tool.args:
			if arg.arg_name in ("a", "b"):
				self.assertEqual(arg.type, "integer")
				self.assertTrue(arg.is_required)

		# Verify echo_message tool schema
		echo_tool = otto.get(OttoTool, "test-dummy-assistant-echo")
		self.assertEqual(len(echo_tool.args), 1)
		message_arg = echo_tool.args[0]
		self.assertEqual(message_arg.arg_name, "message")
		self.assertEqual(message_arg.type, "string")
		self.assertTrue(message_arg.is_required)
