# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from otto.otto.doctype.otto_task.utils import HANDLER_PATH, clear_hooks_cache, update_doc_events

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class UnitTestOttoTask(UnitTestCase):
	"""
	Unit tests for OttoTask.
	Use this class for testing individual functions and methods.
	"""

	def setUp(self):
		self.hooks_path = frappe.get_app_path("otto", "hooks.py")
		try:
			with open(self.hooks_path) as f:
				self.initial_hooks_content = f.read()
		except FileNotFoundError:
			self.skipTest(f"hooks.py not found or could not be read at {self.hooks_path}")
		except OSError as e:
			self.skipTest(f"Error reading hooks.py at {self.hooks_path}: {e}")

		# Ensure hooks file is restored and cache is cleared after the test
		self.addCleanup(self.restore_hooks)

	def restore_hooks(self):
		with open(self.hooks_path, "w") as f:
			f.write(self.initial_hooks_content)
		clear_hooks_cache()

	def test_hooks_doc_events_updates(self):
		# The check for hooks.py existence is now handled in setUp by skipping the test
		if self.initial_hooks_content is None:
			self.skipTest("hooks.py not found, skipping test_update_doc_events")

		test_doctype1 = "ToDo"
		test_event1 = "validate"
		test_doctype2 = "User"
		test_event2 = "after_save"

		# --- Test Adding First Handler ---
		update_doc_events(test_doctype1, test_event1, remove=False)
		doc_events = frappe.get_hooks("doc_events", app_name="otto")
		self.assertIn(
			HANDLER_PATH,
			doc_events.get(test_doctype1, {}).get(test_event1, []),
			f"Handler {HANDLER_PATH} not added to {test_doctype1}.{test_event1}",
		)

		# --- Test Adding Second Handler ---
		update_doc_events(test_doctype2, test_event2, remove=False)
		doc_events = frappe.get_hooks("doc_events", app_name="otto")
		self.assertIn(
			HANDLER_PATH,
			doc_events.get(test_doctype2, {}).get(test_event2, []),
			f"Handler {HANDLER_PATH} not added to {test_doctype2}.{test_event2}",
		)

		# --- Test Removing First Handler ---
		update_doc_events(test_doctype1, test_event1, remove=True)
		doc_events = frappe.get_hooks("doc_events", app_name="otto")
		self.assertNotIn(
			HANDLER_PATH,
			doc_events.get(test_doctype1, {}).get(test_event1, []),
			f"Handler {HANDLER_PATH} not removed from {test_doctype1}.{test_event1}",
		)

		# Check if the second handler still persists
		self.assertIn(
			HANDLER_PATH,
			doc_events.get(test_doctype2, {}).get(test_event2, []),
			f"Handler {HANDLER_PATH} was incorrectly removed from {test_doctype2}.{test_event2}",
		)


class IntegrationTestOttoTask(IntegrationTestCase):
	"""
	Integration tests for OttoTask.
	Use this class for testing interactions between multiple components.
	"""

	pass
