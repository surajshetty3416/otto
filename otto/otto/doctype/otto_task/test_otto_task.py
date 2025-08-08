# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt
from __future__ import annotations

from frappe.tests import IntegrationTestCase, UnitTestCase

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


class IntegrationTestOttoTask(IntegrationTestCase):
	"""
	Integration tests for OttoTask.
	Use this class for testing interactions between multiple components.
	"""

	pass
