# Most of this is cobbled from Frappe Flow server script execution code
from __future__ import annotations

import ast
import importlib
import io
import json
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

import frappe
from frappe.model.document import Document
from frappe.utils.safe_exec import safe_exec
from RestrictedPython import PrintCollector

from otto.utils import json_dumps

"""
Server Script execution task implies that Python code is executed in a Frappe
server script environment:

https://docs.frappe.io/framework/user/en/desk/scripting/server-script

All constraints of a server script apply.
"""

__all__ = [
	"execute",
	"validate",
	"run_get_context",
]

OUT_VAR_NAME = "out"

if TYPE_CHECKING:
	import io

Args = dict[str, Any]


def execute(script: str, *, arg_names: list[str], args: Args) -> ExecutionResult:
	script, globals = get_script_and_globals(script, args, arg_names)

	stdout = io.StringIO()
	stderr = io.StringIO()
	with capture_output(stdout, stderr):
		result = safe_exec(script, globals)
	result = result[0][OUT_VAR_NAME]

	return ExecutionResult(
		result=result,
		stdout=stdout.getvalue(),
		stderr=stderr.getvalue(),
	)


def run_get_context(get_context: str, doc: Document, event: str | None = None) -> str | list[str]:
	if not get_context:
		return doc.as_json()

	script, globals = get_script_and_globals(
		get_context,
		{"doc": doc, "event": event},
		["doc", "event"],
		function_name="get_context",
	)

	stdout = io.StringIO()
	stderr = io.StringIO()
	with capture_output(stdout, stderr):
		result = safe_exec(script, globals)
	result = result[0][OUT_VAR_NAME]
	if isinstance(result, str):
		return result

	if not isinstance(result, list):
		return json_dumps(result)[0]

	return [r if isinstance(r, str) else json_dumps(r)[0] for r in result]


def get_script_and_globals(
	script: str,
	args: Args,
	arg_names: list[str],
	function_name: str = "main",
):
	script, imports = extract_imports(script)
	globals = {"_print_": RegularPrint, **imports}
	if not arg_names:
		script = "\n".join([script, f"{OUT_VAR_NAME} = {function_name}()"])
		return script, globals

	arg_list = []
	for name in arg_names:
		"""
		Validation for when default value is not provided should be handled
		before execute is called in FL Script Task itself.
		"""

		if name not in args:
			continue

		arg_variable_name = f"fl___script_arg_{name}"

		globals[arg_variable_name] = args[name]
		arg_list.append(f"{name}={arg_variable_name}")

	script = "\n".join([script, f"{OUT_VAR_NAME} = {function_name}({', '.join(arg_list)})"])
	return script, globals


def validate(script: str, script_name: str) -> tuple[list[str], list[ArgDefinition]]:
	"""
	Validate a server script by checking the script AST.

	Returns a tuple of (invalidation_reasons, args_def).
	"""
	try:
		tree = ast.parse(script, filename=script_name, feature_version=(3, 11))
	except IndentationError as e:
		reason = str(e)
		reason = reason[0].upper() + reason[1:]
		return [reason], []

	main_function_node: None | ast.FunctionDef = None
	invalidation_reasons: list[str] = []

	for node in ast.walk(tree):
		if isinstance(node, ast.FunctionDef) and node.name == "main" and node in tree.body:
			main_function_node = node

		# Check if main() is called directly
		elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "main":
			invalidation_reasons.append(f"Direct calls to main() are not allowed (line: {node.lineno})")

		# # Check if imports are used
		# elif isinstance(node, ast.Import | ast.ImportFrom):
		# 	invalidation_reasons.append(f"Imports are not allowed (line: {node.lineno})")

	if main_function_node is None:
		invalidation_reasons.append("Script must contain a 'main' function definition")
	else:
		invalidation_reasons.extend(validate_main_function(main_function_node))

	if invalidation_reasons or main_function_node is None:
		return invalidation_reasons, []

	try:
		compile(script, "<ast>", "exec")
	except SyntaxError as e:
		invalidation_reasons.append(f"Invalid Python syntax: {e!s}")
		return invalidation_reasons, []

	return invalidation_reasons, get_args_def(main_function_node)


def validate_main_function(main_function_node: ast.FunctionDef):
	invalidation_reasons = validate_method_args(main_function_node)
	args = main_function_node.args

	for d in args.defaults:
		if isinstance(d, ast.Constant):
			continue

		invalidation_reasons.append(
			f"Default value '{ast.unparse(d)}' is invalid, only constants are allowed"
		)

	return invalidation_reasons


class RegularPrint(PrintCollector):
	"""
	Used to restore `print` functionality in restricted execution.
	"""

	def _call_print(self, *args, **kwargs):
		print(*args, **kwargs)


NO_RESULT = object()


class ExecutionResult(TypedDict):
	"""Result of executing a server script."""

	result: Any  # return value from the main() function or result of control task
	stdout: str  # standard output during execution
	stderr: str  # standard error during execution


AllowedArgTypes = Literal["str", "int", "float", "bool", "list", "dict", "unknown", "Document"]
allowed_arg_types = ["str", "int", "float", "bool", "list", "dict"]


class ArgDefinition(TypedDict):
	name: str
	type: AllowedArgTypes
	default: str | None  # JSON of the default value
	has_default: bool


def validate_method_args(main_function_node: ast.FunctionDef):
	invalidation_reasons: list[str] = []
	args = main_function_node.args

	if args.kwarg is not None:
		invalidation_reasons.append("method must not accept wildcard keyword arguments (**kwargs)")

	if args.vararg is not None:
		invalidation_reasons.append("method must not accept variable arguments (*args)")

	return invalidation_reasons


def get_args_def(main_function_node: ast.FunctionDef) -> list[ArgDefinition]:
	arg_defaults = [*main_function_node.args.defaults]
	arg_defaults.reverse()

	arg_list: list[ArgDefinition] = []

	args = [*main_function_node.args.args]
	args.reverse()
	for i, a in enumerate(args):
		name = a.arg
		assert isinstance(name, str), f"name {name} is of type {type(name)}"

		default = None

		if len(arg_defaults) > i:
			default = get_def_value(arg_defaults[i])

		arg_list.append(
			{
				"name": name,
				"type": get_arg_type(a),
				"default": default,
				"has_default": default is not None,
			}
		)

	arg_list.reverse()
	return arg_list


def get_def_value(default: ast.expr):
	assert isinstance(default, ast.Constant), "default value must be an ast.Constant"
	return json.dumps(default.value)


def get_arg_type(arg: ast.arg) -> AllowedArgTypes:
	if (
		isinstance(arg.annotation, ast.Constant)
		and isinstance(arg.annotation.value, str)
		and arg.annotation.value in allowed_arg_types
	):
		return cast("AllowedArgTypes", arg.annotation.value)

	if isinstance(arg.annotation, ast.Name) and arg.annotation.id in allowed_arg_types:
		return cast("AllowedArgTypes", arg.annotation.id)

	return "unknown"


@contextmanager
def capture_output(stdout: io.StringIO, stderr: io.StringIO):
	old_stdout = sys.stdout
	old_stderr = sys.stderr

	sys.stdout = stdout
	sys.stderr = stderr

	try:
		yield
	finally:
		sys.stdout = old_stdout
		sys.stderr = old_stderr


def extract_imports(script: str) -> tuple[str, dict[str, Any]]:
	"""
	Extract import statements from a Python script, remove them from the script,
	and import the modules if they pass security checks.

	Args:
		script: The Python script as a string

	Returns:
		A tuple containing:
		- The script with import statements removed
		- A dictionary of imported modules/objects
	"""
	try:
		tree = ast.parse(script)
	except SyntaxError:
		# If script has syntax errors, return it unchanged with empty imports
		return script, {}

	imports = {}
	import_nodes = []

	# Find all import nodes
	for node in ast.iter_child_nodes(tree):
		if isinstance(node, ast.Import | ast.ImportFrom):
			import_nodes.append(node)

	# Remove import nodes from the AST
	tree.body = [node for node in tree.body if node not in import_nodes]

	# Convert modified AST back to source code
	modified_script = ast.unparse(tree)

	# Process the imports
	for node in import_nodes:
		if isinstance(node, ast.Import):
			for name in node.names:
				module_name = name.name
				as_name = name.asname or module_name

				# Security check - only allow specific modules
				if _is_safe_import(module_name):
					try:
						imports[as_name] = importlib.import_module(module_name)
					except ImportError:
						pass

		elif isinstance(node, ast.ImportFrom):
			module_name = node.module
			if module_name and _is_safe_import(module_name):
				try:
					module = importlib.import_module(module_name)
					for name in node.names:
						attr_name = name.name
						as_name = name.asname or attr_name

						if hasattr(module, attr_name):
							imports[as_name] = getattr(module, attr_name)
				except ImportError:
					pass

	return modified_script, imports


def _is_safe_import(module_name: str) -> bool:
	"""
	Check if a module is safe to import.

	Args:
		module_name: The name of the module to check

	Returns:
		True if the module is safe to import, False otherwise
	"""
	if "otto" in module_name:
		return True

	# List of allowed modules
	allowed_modules = {
		"datetime",
		"json",
		"math",
		"re",
		"time",
		"uuid",
		"collections",
		"itertools",
		"functools",
		"typing",
		"decimal",
		"fractions",
		"statistics",
		"random",
		"csv",
		"pathlib",
		"urllib.parse",
		"base64",
		"hashlib",
		"hmac",
		"zlib",
		"gzip",
		"zipfile",
		"requests",
	}

	# Check if the module or its parent is in the allowed list
	parts = module_name.split(".")
	for i in range(len(parts)):
		prefix = ".".join(parts[: i + 1])
		if prefix in allowed_modules:
			return True

	return False
