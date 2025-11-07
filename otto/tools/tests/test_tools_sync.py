# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import contextlib

import frappe
from frappe.tests import UnitTestCase

import otto
from otto.otto.doctype.otto_tool.otto_tool import OttoTool
from otto.tools import sync_tool, sync_tools


class TestToolSync(UnitTestCase):
	"""
	Tests for tool synchronization via sync_tool and sync_tools functions.
	Tests that tools are correctly created/updated from tool modules.
	"""

	def setUp(self):
		"""Set up test fixtures."""
		self.created_tools: list[str] = []

	def tearDown(self):
		"""Clean up created test resources."""
		# Clean up tools
		for tool_name in self.created_tools:
			with contextlib.suppress(Exception):
				if frappe.db.exists("Otto Tool", tool_name):
					frappe.delete_doc("Otto Tool", tool_name, force=True)

	def test_sync_tool_creates_new_tool(self):
		"""Test that sync_tool creates a new tool from a module."""
		from otto.tools.tests import add_tool

		# Sync the tool
		result = sync_tool(add_tool)

		# Track for cleanup
		self.created_tools.append("test-tools-add")

		# Verify tool was created
		self.assertIsNotNone(result)
		self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-add"))

		# Load and verify tool
		tool = otto.get(OttoTool, "test-tools-add")
		self.assertEqual(tool.title, "Add Numbers")
		self.assertEqual(tool.slug, "add")
		self.assertTrue(tool.is_valid)
		self.assertTrue(tool.is_app_defined)
		self.assertFalse(tool.requires_permission)
		self.assertFalse(tool.use_explanation)

		# Verify tool has correct schema
		self.assertEqual(len(tool.args), 2)
		arg_names = {arg.arg_name for arg in tool.args}
		self.assertIn("a", arg_names)
		self.assertIn("b", arg_names)

		# Check specific arg details
		for arg in tool.args:
			if arg.arg_name in ("a", "b"):
				self.assertEqual(arg.type, "integer")
				self.assertTrue(arg.is_required)

	def test_sync_tool_updates_existing_tool(self):
		"""Test that sync_tool updates an existing tool."""
		from otto.tools.tests import add_tool

		# First sync
		sync_tool(add_tool)
		self.created_tools.append("test-tools-add")

		# Modify the tool
		tool = otto.get(OttoTool, "test-tools-add")
		tool.title = "Modified Title"
		tool.save()

		# Sync again
		sync_tool(add_tool)

		# Verify tool was updated back to original
		tool.reload()
		self.assertEqual(tool.title, "Add Numbers")
		self.assertTrue(tool.is_app_defined)

	def test_sync_tool_with_string_path(self):
		"""Test that sync_tool works with string module path."""
		# Sync using string path
		result = sync_tool("otto.tools.tests.add_tool")

		# Track for cleanup
		self.created_tools.append("test-tools-add")

		# Verify tool was created
		self.assertIsNotNone(result)
		self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-add"))

		tool = otto.get(OttoTool, "test-tools-add")
		self.assertEqual(tool.title, "Add Numbers")
		self.assertEqual(tool.slug, "add")

	def test_sync_tool_with_requires_permission(self):
		"""Test that sync_tool correctly handles requires_permission attribute."""
		from otto.tools.tests import multiply_tool

		# Sync the tool
		sync_tool(multiply_tool)
		self.created_tools.append("test-tools-multiply")

		# Verify tool has requires_permission set
		tool = otto.get(OttoTool, "test-tools-multiply")
		self.assertTrue(tool.requires_permission)
		self.assertTrue(tool.use_explanation)
		self.assertEqual(tool.slug, "multiply")

	def test_sync_tool_with_use_explanation(self):
		"""Test that sync_tool correctly handles use_explanation attribute."""
		from otto.tools.tests import multiply_tool

		# Sync the tool
		sync_tool(multiply_tool)
		self.created_tools.append("test-tools-multiply")

		# Verify tool has use_explanation set
		tool = otto.get(OttoTool, "test-tools-multiply")
		self.assertTrue(tool.use_explanation)

	def test_sync_tool_with_dev_mode_only(self):
		"""Test that sync_tool respects dev_mode_only attribute."""
		from otto.tools.tests import dev_tool

		# Save original developer mode setting
		original_dev_mode = frappe.conf.developer_mode

		try:
			# Test with developer_mode = False
			frappe.conf.developer_mode = False
			result = sync_tool(dev_tool)

			# Tool should not be created in non-dev mode
			self.assertIsNone(result)
			self.assertFalse(frappe.db.exists("Otto Tool", "test-tools-dev"))

			# Test with developer_mode = True
			frappe.conf.developer_mode = True
			result = sync_tool(dev_tool)
			self.created_tools.append("test-tools-dev")

			# Tool should be created in dev mode
			self.assertIsNotNone(result)
			self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-dev"))

		finally:
			# Restore original developer mode
			frappe.conf.developer_mode = original_dev_mode

	def test_sync_tool_import_path(self):
		"""Test that tool import path is correctly set."""
		from otto.tools.tests import add_tool

		# Sync the tool
		sync_tool(add_tool)
		self.created_tools.append("test-tools-add")

		# Verify tool import path
		tool = otto.get(OttoTool, "test-tools-add")
		self.assertIsNotNone(tool.tool_import_path)
		assert tool.tool_import_path is not None
		self.assertIn("add", tool.tool_import_path)

	def test_sync_tool_schema_correctly_set(self):
		"""Test that tool schema (args) is correctly set."""
		from otto.tools.tests import multiply_tool

		# Sync the tool
		sync_tool(multiply_tool)
		self.created_tools.append("test-tools-multiply")

		# Verify tool schema
		tool = otto.get(OttoTool, "test-tools-multiply")
		self.assertEqual(len(tool.args), 2)

		arg_names = {arg.arg_name for arg in tool.args}
		self.assertIn("x", arg_names)
		self.assertIn("y", arg_names)

		# Check specific arg details
		for arg in tool.args:
			if arg.arg_name in ("x", "y"):
				self.assertEqual(arg.type, "integer")
				self.assertTrue(arg.is_required)

	def test_sync_tool_description_from_docstring(self):
		"""Test that tool description is extracted from function docstring."""
		from otto.tools.tests import add_tool

		# Sync the tool
		sync_tool(add_tool)
		self.created_tools.append("test-tools-add")

		# Verify tool description
		tool = otto.get(OttoTool, "test-tools-add")
		self.assertIsNotNone(tool.description)
		assert tool.description is not None
		self.assertIn("Add two numbers", tool.description)

	def test_sync_tool_updates_all_fields(self):
		"""Test that sync_tool updates all fields when syncing existing tool."""
		from otto.tools.tests import add_tool

		# First sync
		sync_tool(add_tool)
		self.created_tools.append("test-tools-add")

		# Modify multiple fields
		tool = otto.get(OttoTool, "test-tools-add")
		tool.title = "Modified Title"
		tool.description = "Modified Description"
		tool.slug = "modified_slug"
		tool.requires_permission = True
		tool.is_valid = False
		tool.is_external = True
		tool.save()

		# Sync again
		sync_tool(add_tool)

		# Verify all fields were updated back
		tool.reload()
		self.assertEqual(tool.title, "Add Numbers")
		self.assertEqual(tool.slug, "add")
		self.assertFalse(tool.requires_permission)
		self.assertTrue(tool.is_valid)
		self.assertFalse(tool.is_external)
		self.assertTrue(tool.is_app_defined)

	def test_sync_tools_multiple_tools(self):
		"""Test syncing multiple tools at once using sync_tools."""
		from otto.tools.tests import add_tool, multiply_tool

		# Sync multiple tools
		sync_tools([add_tool, multiply_tool])

		# Track for cleanup
		self.created_tools.extend(["test-tools-add", "test-tools-multiply"])

		# Verify both tools were created
		self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-add"))
		self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-multiply"))

		# Verify add tool
		add_tool = otto.get(OttoTool, "test-tools-add")
		self.assertEqual(add_tool.title, "Add Numbers")

		# Verify multiply tool
		multiply_tool = otto.get(OttoTool, "test-tools-multiply")
		self.assertEqual(multiply_tool.title, "Multiply Numbers")

	def test_sync_tools_with_string_paths(self):
		"""Test syncing tools using string paths."""
		# Sync tools using string paths
		sync_tools(
			[
				"otto.tools.tests.add_tool",
				"otto.tools.tests.multiply_tool",
			]
		)

		# Track for cleanup
		self.created_tools.extend(["test-tools-add", "test-tools-multiply"])

		# Verify both tools were created
		self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-add"))
		self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-multiply"))

	def test_sync_tools_with_invalid_module_graceful_failure(self):
		"""Test that sync_tools handles invalid modules gracefully."""
		# This should not raise an exception, just log an error
		sync_tools(["otto.tools.tests.nonexistent_module"])

		# No cleanup needed since nothing was created

	def test_sync_tools_mixed_valid_invalid(self):
		"""Test that sync_tools continues processing after an invalid module."""
		from otto.tools.tests import add_tool

		# Sync with one valid and one invalid module
		sync_tools(["otto.tools.tests.nonexistent_module", add_tool])

		# Track for cleanup
		self.created_tools.append("test-tools-add")

		# Verify valid tool was created despite invalid one
		self.assertTrue(frappe.db.exists("Otto Tool", "test-tools-add"))

	def test_sync_tool_function_inference(self):
		"""Test that tool function is correctly inferred from module."""
		from otto.tools.tests import add_tool

		# The test_add_tool module has a function named 'add' matching the tool name
		sync_tool(add_tool)
		self.created_tools.append("test-tools-add")

		# Verify tool was created and is callable
		tool = otto.get(OttoTool, "test-tools-add")
		self.assertIsNotNone(tool.tool_import_path)
		assert tool.tool_import_path is not None
		self.assertIn("add", tool.tool_import_path)

	def test_sync_tool_marks_as_app_defined(self):
		"""Test that synced tools are marked as app-defined."""
		from otto.tools.tests import add_tool

		# Sync the tool
		sync_tool(add_tool)
		self.created_tools.append("test-tools-add")

		# Verify tool is marked as app-defined
		tool = otto.get(OttoTool, "test-tools-add")
		self.assertTrue(tool.is_app_defined)
		self.assertFalse(tool.is_external)
		self.assertTrue(tool.is_valid)

	def test_sync_tool_clears_invalid_state(self):
		"""Test that syncing clears any invalid state from a tool."""
		from otto.tools.tests import add_tool

		# First sync
		sync_tool(add_tool)
		self.created_tools.append("test-tools-add")

		# Mark tool as invalid
		tool = otto.get(OttoTool, "test-tools-add")
		tool.is_valid = False
		tool.reason = "Some error reason"
		tool.save()

		# Sync again
		sync_tool(add_tool)

		# Verify invalid state was cleared
		tool.reload()
		self.assertTrue(tool.is_valid)
		self.assertIsNone(tool.reason)

	def test_sync_tool_idempotent(self):
		"""Test that sync_tool is idempotent - calling multiple times is safe."""
		from otto.tools.tests import add_tool

		# Sync the tool multiple times
		result1 = sync_tool(add_tool)
		result2 = sync_tool(add_tool)
		result3 = sync_tool(add_tool)

		self.created_tools.append("test-tools-add")

		# All results should be the same
		self.assertEqual(result1, result2)
		self.assertEqual(result2, result3)

		# Tool should still be valid
		tool = otto.get(OttoTool, "test-tools-add")
		self.assertTrue(tool.is_valid)
		self.assertEqual(tool.title, "Add Numbers")
