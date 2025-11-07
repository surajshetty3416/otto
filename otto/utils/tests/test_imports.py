# Copyright (c) 2025, Alan Tom and Contributors
# See license.txt

import tempfile
from pathlib import Path
from textwrap import dedent as dd

from frappe.tests import UnitTestCase

from otto.utils.imports import get_import_path, import_fn, import_module


class TestImports(UnitTestCase):
	"""
	Tests for import utilities to ensure proper importing of modules and functions
	from both internal (app-based) and external (filesystem) locations.
	"""

	def test_get_import_path_and_import_fn_roundtrip_internal(self):
		"""Test that get_import_path and import_fn work together for internal functions."""
		# Test with an internal function from the otto app
		from otto.utils.imports import get_import_path as test_fn

		# Get the import path
		import_path = get_import_path(test_fn)

		# The import path should be a dotted path for internal functions
		self.assertTrue("." in import_path)
		self.assertFalse("/" in import_path)
		self.assertFalse(":" in import_path)

		# Import the function using the path
		imported_fn = import_fn(import_path)

		# Should be the same function
		self.assertIs(imported_fn, test_fn)

	def test_get_import_path_and_import_fn_roundtrip_external_single_file(self):
		"""Test get_import_path and import_fn for external single-file modules."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a single file module with a function
			module_file = Path(tmpdir) / "test_module.py"
			module_file.write_text(
				dd("""
				def external_function(x, y):
					return x + y

				def another_function():
					return "hello"
				""")
			)

			# Import the function from the external module
			module_path = f"{module_file.as_posix()}:external_function"
			imported_fn = import_fn(module_path)

			# Get the import path
			import_path = get_import_path(imported_fn)

			# The import path should be a file path for external functions
			self.assertIn(":", import_path)
			self.assertTrue(import_path.startswith("/"))

			# Re-import using the generated path
			reimported_fn = import_fn(import_path)

			# Should have the same name and behavior
			self.assertEqual(reimported_fn.__name__, imported_fn.__name__)
			self.assertEqual(reimported_fn(2, 3), 5)
			self.assertEqual(imported_fn(2, 3), 5)

	def test_get_import_path_and_import_fn_roundtrip_external_package(self):
		"""Test get_import_path and import_fn for external package modules."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a package with __init__.py
			package_dir = Path(tmpdir) / "test_package_two"
			package_dir.unlink(missing_ok=True)
			package_dir.mkdir()
			init_file = package_dir / "__init__.py"
			init_file.write_text(
				dd("""
				def package_function(value):
					return value * 2

				class PackageClass:
					def method(self):
						return "from package"
				""")
			)

			# Import the function from the package
			module_path = f"{package_dir.as_posix()}:package_function"
			imported_fn = import_fn(module_path)

			# Get the import path
			import_path = get_import_path(imported_fn)

			# The import path should be a file path pointing to __init__.py
			self.assertIn(":", import_path)
			self.assertTrue(import_path.startswith("/"))

			# Re-import using the generated path
			reimported_fn = import_fn(import_path)

			# Should have the same name and behavior
			self.assertEqual(reimported_fn.__name__, imported_fn.__name__)
			self.assertEqual(reimported_fn(5), 10)
			self.assertEqual(imported_fn(5), 10)

	def test_import_module_internal_dotted_path(self):
		"""Test that import_module can import internal modules using dotted paths."""
		# Import a known internal module
		module = import_module("otto.utils.imports")

		# Should have the expected attributes
		self.assertTrue(hasattr(module, "get_import_path"))
		self.assertTrue(hasattr(module, "import_fn"))
		self.assertTrue(hasattr(module, "import_module"))

		# Check module name
		self.assertEqual(module.__name__, "otto.utils.imports")

	def test_import_module_external_single_file(self):
		"""Test that import_module can import external single-file modules."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a single file module
			module_file = Path(tmpdir) / "single_module.py"
			module_file.write_text(
				dd("""
				# Test module
				MODULE_CONSTANT = "test_value"

				def module_function():
					return "from single module"

				class ModuleClass:
					pass
				""")
			)

			# Import the module using file path
			module = import_module(str(module_file))

			# Check module attributes
			self.assertTrue(hasattr(module, "MODULE_CONSTANT"))
			self.assertTrue(hasattr(module, "module_function"))
			self.assertTrue(hasattr(module, "ModuleClass"))

			# Check values
			self.assertEqual(module.MODULE_CONSTANT, "test_value")
			self.assertEqual(module.module_function(), "from single module")

			# Module name should be the file name without extension
			self.assertEqual(module.__name__, "single_module")

	def test_import_module_external_package(self):
		"""Test that import_module can import external package modules."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a package
			package_dir = Path(tmpdir) / "test_package"
			package_dir.mkdir()
			init_file = package_dir / "__init__.py"
			init_file.write_text(
				dd("""
				# Package initialization
				PACKAGE_VERSION = "1.0.0"

				def package_init_function():
					return "initialized"
				""")
			)

			# Import the package using directory path
			module = import_module(str(package_dir))

			# Check package attributes
			self.assertTrue(hasattr(module, "PACKAGE_VERSION"))
			self.assertTrue(hasattr(module, "package_init_function"))

			# Check values
			self.assertEqual(module.PACKAGE_VERSION, "1.0.0")
			self.assertEqual(module.package_init_function(), "initialized")

			# Module name should be the package name
			self.assertEqual(module.__name__, "test_package")

	def test_import_module_external_package_via_init_file(self):
		"""Test that import_module works when given path to __init__.py directly."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a package
			package_dir = Path(tmpdir) / "my_package"
			package_dir.mkdir()
			init_file = package_dir / "__init__.py"
			init_file.write_text(
				dd("""
				INIT_VAR = "from init"
				""")
			)

			# Import using the __init__.py file path directly
			module = import_module(str(init_file))

			# Should work the same as importing the directory
			self.assertTrue(hasattr(module, "INIT_VAR"))
			self.assertEqual(module.INIT_VAR, "from init")

			# Module name should be the package name, not __init__
			self.assertEqual(module.__name__, "my_package")

	def test_import_fn_with_dotted_path(self):
		"""Test that import_fn can import functions using dotted paths."""
		# Import a known function using dotted path
		fn = import_fn("otto.utils.imports.get_import_path")

		# Should be callable
		self.assertTrue(callable(fn))

		# Should be the correct function
		from otto.utils.imports import get_import_path

		self.assertIs(fn, get_import_path)

	def test_import_fn_with_file_path(self):
		"""Test that import_fn can import functions using file paths."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a module with a function
			module_file = Path(tmpdir) / "file_module.py"
			module_file.write_text(
				dd("""
				def my_function(a, b):
					return a - b
				""")
			)

			# Import using file path
			path = f"{module_file.as_posix()}:my_function"
			fn = import_fn(path)

			# Should be callable and work correctly
			self.assertTrue(callable(fn))
			self.assertEqual(fn.__name__, "my_function")
			self.assertEqual(fn(10, 3), 7)

	def test_import_fn_nested_class_static_method_throws(self):
		"""Test importing methods from classes (using __qualname__)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a module with a class
			module_file = Path(tmpdir) / "class_module.py"
			module_file.write_text(
				dd("""
				class MyClass:
					def my_method(self):
						return "method called"

					@staticmethod
					def static_method():
						return "static called"
				""")
			)

			path = f"{module_file.as_posix()}:MyClass.static_method"

			with self.assertRaises(ValueError):
				import_fn(path)

	def test_import_fn_error_invalid_path(self):
		"""Test that import_fn raises appropriate errors for invalid paths."""
		with self.assertRaises(ValueError):
			# Path with no separator
			import_fn("invalidpath")

	def test_import_fn_error_function_not_found(self):
		"""Test that import_fn raises error when function doesn't exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			module_file = Path(tmpdir) / "empty_module.py"
			module_file.write_text("# Empty module\n")

			with self.assertRaises(ValueError) as context:
				import_fn(f"{module_file.as_posix()}:nonexistent_function")

			self.assertIn("Could not find function", str(context.exception))

	def test_import_fn_error_not_callable(self):
		"""Test that import_fn raises error when imported attribute is not callable."""
		with tempfile.TemporaryDirectory() as tmpdir:
			module_file = Path(tmpdir) / "constants_module.py"
			module_file.write_text("MY_CONSTANT = 42\n")

			with self.assertRaises(ValueError) as context:
				import_fn(f"{module_file.as_posix()}:MY_CONSTANT")

			self.assertIn("is not callable", str(context.exception))

	def test_import_module_error_invalid_path(self):
		"""Test that import_module raises error for invalid paths."""
		with self.assertRaises(ValueError):
			# Not a valid dotted path or file path
			import_module("invalid-path-with-dashes")

	def test_import_module_error_file_not_found(self):
		"""Test that import_module raises error when file doesn't exist."""
		with self.assertRaises(FileNotFoundError):
			import_module("/nonexistent/path/to/module.py")

	def test_external_module_with_dependencies(self):
		"""Test importing external modules that have internal dependencies."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a package with multiple files
			package_dir = Path(tmpdir) / "complex_package"
			package_dir.mkdir()

			# Create __init__.py
			init_file = package_dir / "__init__.py"
			init_file.write_text(
				dd("""
				from .helper import helper_function

				def main_function():
					return helper_function()
				""")
			)

			# Create helper.py
			helper_file = package_dir / "helper.py"
			helper_file.write_text(
				dd("""
				def helper_function():
					return "helper result"
				""")
			)

			# Import the package
			module = import_module(str(package_dir))

			# Should be able to use the function that depends on helper
			self.assertTrue(hasattr(module, "main_function"))
			self.assertEqual(module.main_function(), "helper result")

	def test_roundtrip_preserves_function_attributes(self):
		"""Test that get_import_path + import_fn preserves function attributes."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create a module with a well-documented function
			module_file = Path(tmpdir) / "documented.py"
			module_file.write_text(
				dd('''
				def documented_function(x: int, y: int) -> int:
					"""Add two numbers together.

					Args:
						x: First number
						y: Second number

					Returns:
						Sum of x and y
					"""
					return x + y
				''')
			)

			# Import, get path, and re-import
			original_fn = import_fn(f"{module_file.as_posix()}:documented_function")
			import_path = get_import_path(original_fn)
			reimported_fn = import_fn(import_path)

			# Check that attributes are preserved
			self.assertEqual(reimported_fn.__name__, "documented_function")
			self.assertIsNotNone(reimported_fn.__doc__)
			self.assertIn("Add two numbers", reimported_fn.__doc__ or "")

			# Function should still work
			self.assertEqual(reimported_fn(5, 7), 12)
