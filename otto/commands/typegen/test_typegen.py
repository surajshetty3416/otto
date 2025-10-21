import ast
import unittest
from pathlib import Path

from otto.commands.typegen.api import (
	Param,
	extract_function_info,
	get_func_str,
	get_typescript_type,
)
from otto.commands.typegen.common import (
	FOUND_TYPES,
	handle_subscript,
	handle_typed_dict,
	populate_found_types_for_file,
)


def get_subscript_ast(type_str: str) -> ast.Subscript:
	"""
	Get the ast.Subscript node from a type string.
	"""
	tree = ast.parse(type_str)
	expr = tree.body[0]
	assert isinstance(expr, ast.Expr)
	value = expr.value
	assert isinstance(value, ast.Subscript)
	return value


def get_annotation_ast(type_str: str) -> ast.expr:
	"""Get the AST node for a type annotation."""
	v = ast.parse(type_str).body[0]
	assert isinstance(v, ast.Expr)
	return v.value


class TestTypegen(unittest.TestCase):
	def test_handle_list_subscript(self):
		"""Test handling of list type annotations"""
		test_cases = [
			("list[str]", "string[]"),
			("list[int]", "number[]"),
			("list[bool]", "boolean[]"),
			("list[dict[str, int]]", "Record<string, number>[]"),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				subscript = get_subscript_ast(python_type)
				result = handle_subscript(subscript)
				self.assertEqual(result, expected_ts_type)

	def test_handle_dict_subscript(self):
		"""Test handling of dict type annotations"""
		test_cases = [
			("dict[int, str]", "Record<string, string>"),
			("dict[str, str]", "Record<string, string>"),
			("dict[str, int]", "Record<string, number>"),
			("dict[str, bool]", "Record<string, boolean>"),
			("dict[str, list[int]]", "Record<string, number[]>"),
			(
				"dict[str, dict[int, str]]",
				"Record<string, Record<string, string>>",
			),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				subscript = get_subscript_ast(python_type)
				result = handle_subscript(subscript)
				self.assertEqual(result, expected_ts_type)

	def test_handle_invalid_subscripts(self):
		"""Test handling of invalid or unsupported type annotations"""
		test_cases = [
			("list[tuple[int, str]]", "unknown[]"),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				subscript = get_subscript_ast(python_type)
				result = handle_subscript(subscript)
				self.assertEqual(result, expected_ts_type)

	def test_get_typescript_type_basic(self):
		"""Test conversion of basic Python types to TypeScript"""
		test_cases = [
			("str", "string"),
			("int", "number"),
			("float", "number"),
			("bool", "boolean"),
			("None", "null"),
			("list", "unknown[]"),
			("dict", "Record<string, unknown>"),
			("tuple", "unknown[]"),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				annotation = get_annotation_ast(python_type)
				result = get_typescript_type(annotation)
				self.assertEqual(result, expected_ts_type)

	def test_get_typescript_type_constants(self):
		"""Test conversion of constant values in type annotations"""
		test_cases = [
			("None", "null"),
			('"str"', "string"),
			('"int"', "number"),
			('"bool"', "boolean"),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				annotation = get_annotation_ast(python_type)
				result = get_typescript_type(annotation)
				self.assertEqual(result, expected_ts_type)

	def test_get_typescript_type_complex(self):
		"""Test conversion of complex type annotations"""
		test_cases = [
			# Nested lists
			("list[list[str]]", "string[][]"),
			("list[list[int]]", "number[][]"),
			# Complex dictionaries
			("dict[str, list[int]]", "Record<string, number[]>"),
			("dict[str, dict[str, str]]", "Record<string, Record<string, string>>"),
			# Mixed types
			("list[dict[str, list[int]]]", "Record<string, number[]>[]"),
			(
				"dict[str, list[dict[str, int]]]",
				"Record<string, Record<string, number>[]>",
			),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				annotation = get_annotation_ast(python_type)
				result = get_typescript_type(annotation)
				self.assertEqual(result, expected_ts_type)

	def test_get_typescript_type_unsupported(self):
		"""Test handling of unsupported or invalid type annotations"""
		test_cases = [
			# Custom types
			"MyCustomType",
			"Optional[str]",  # Union types not supported yet
			"Union[str, int]",  # Union types not supported yet
			"Any",  # Any type
		]

		for python_type in test_cases:
			with self.subTest(python_type=python_type):
				annotation = get_annotation_ast(python_type)
				result = get_typescript_type(annotation)
				self.assertEqual(result, "unknown")

	def test_get_typescript_type_literal(self):
		"""Test conversion of Literal types to TypeScript"""
		test_cases = [
			('Literal["Success"]', '"Success"'),
			('Literal["Success", "Failure"]', '"Success" | "Failure"'),
			("Literal[1, 2, 3]", "1 | 2 | 3"),
			("Literal[True, False]", "true | false"),
			('Literal["one", 2, True]', '"one" | 2 | true'),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				annotation = get_annotation_ast(python_type)
				result = get_typescript_type(annotation)
				self.assertEqual(result, expected_ts_type)

	def test_get_typescript_type_union(self):
		"""Test conversion of union types to TypeScript"""
		test_cases = [
			("str | None", "string | null"),
			("None | str", "null | string"),
			("int | None", "number | null"),
			("None | int", "null | number"),
			("bool | None", "boolean | null"),
			("None | bool", "null | boolean"),
			("str | int", "string | number"),
			("int | str", "number | string"),
			("str | int | None", "string | number | null"),
			("None | str | int", "null | string | number"),
		]

		for python_type, expected_ts_type in test_cases:
			with self.subTest(python_type=python_type):
				annotation = get_annotation_ast(python_type)
				result = get_typescript_type(annotation)
				self.assertEqual(result, expected_ts_type)

	def test_extract_function_info(self):
		"""Test extraction of function information including optional parameters"""
		# Create a test function AST
		code = """def example(x: str | None, y: str = "default") -> str | None: pass"""
		tree = ast.parse(code)
		func_def = tree.body[0]
		assert isinstance(func_def, ast.FunctionDef)

		# Test function info extraction
		func_info = extract_function_info(func_def, Path("test.py"), False)

		# Verify parameters
		self.assertEqual(func_info.name, "example")
		self.assertEqual(len(func_info.params), 2)
		self.assertEqual(func_info.params[0], Param("x", "string | null"))
		self.assertEqual(func_info.params[1], Param("y", "string<OPTIONAL>"))
		self.assertEqual(func_info.return_type, "string | null")
		self.assertFalse(func_info.allow_guest)
		self.assertEqual(
			get_func_str(func_info),
			"example(args: {x: string | null, y?: string}): Call<string | null>;",
		)

		# Test function with no optional parameters
		code = """def simple(x: str, y: int) -> bool: pass"""
		tree = ast.parse(code)
		func_def = tree.body[0]
		assert isinstance(func_def, ast.FunctionDef)

		func_info = extract_function_info(func_def, Path("test.py"), False)

		self.assertEqual(func_info.name, "simple")
		self.assertEqual(len(func_info.params), 2)
		self.assertEqual(func_info.params[0], Param("x", "string"))
		self.assertEqual(func_info.params[1], Param("y", "number"))
		self.assertEqual(func_info.return_type, "boolean")
		self.assertFalse(func_info.allow_guest)

	def test_handle_typed_dict(self):
		"""Test conversion of TypedDict classes to TypeScript interfaces"""

		# Test with nested TypedDict
		code = """
class NestedResponse(TypedDict):
    data: APIResponse
    timestamp: int
"""
		tree = ast.parse(code)
		class_def = tree.body[0]
		assert isinstance(class_def, ast.ClassDef)

		expected = """export interface NestedResponse {
  data: APIResponse;
  timestamp: number;
}
"""
		result = handle_typed_dict(class_def)
		self.assertEqual(result, expected)

	def test_find_typed_dicts(self):
		"""Test finding TypedDict classes in a file"""
		code = """
from typing import TypedDict, Literal, Any

class APIResponse(TypedDict):
    status: Literal["Success", "Failure"]
    message: str
    reasons: list[str] | None
    data: Any | None

class NotATypedDict:
    x: int

class AnotherResponse(TypedDict):
    code: int
    message: str
"""
		import tempfile

		with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
			temp_path = Path(temp_file.name)
			with temp_path.open("w") as f:
				f.write(code)

		typed_dicts = populate_found_types_for_file(temp_path)
		self.assertEqual(len(typed_dicts), 2)
		self.assertIn("APIResponse", typed_dicts)
		self.assertIn("AnotherResponse", typed_dicts)
		self.assertNotIn("NotATypedDict", typed_dicts)
		self.assertIn("APIResponse", FOUND_TYPES)
		self.assertIn("AnotherResponse", FOUND_TYPES)

		code = """
class APIResponse(TypedDict):
    status: Literal["Success", "Failure"]
    message: str
    reasons: list[str] | None
    data: Any | None
"""
		tree = ast.parse(code)
		class_def = tree.body[0]
		assert isinstance(class_def, ast.ClassDef)

		expected = """export interface APIResponse {
  status: "Success" | "Failure";
  message: string;
  reasons: string[] | null;
  data: unknown | null;
}
"""
		result = handle_typed_dict(class_def)
		self.assertEqual(result, expected)
