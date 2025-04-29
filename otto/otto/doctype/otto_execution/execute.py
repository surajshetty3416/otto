# Most of this is cobbled from Frappe Flow server script execution code
from __future__ import annotations

import ast
import io
import json
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

import frappe
from frappe.model.document import Document
from frappe.utils.safe_exec import safe_exec
from RestrictedPython import PrintCollector

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


def execute(script: str, *, args_def: list[ArgDefinition], args: Args) -> ExecutionResult:
	script, globals = get_script_and_globals(script, args_def, args)

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

	args_def: list[ArgDefinition] = [
		{
			"name": "doc",
			"type": "Document",
			"default": None,
			"has_default": False,
		},
		{
			"name": "event",
			"type": "str",
			"default": None,
			"has_default": False,
		},
	]

	script, globals = get_script_and_globals(
		get_context,
		args_def,
		{"doc": doc, "event": event},
		function_name="get_context",
	)

	stdout = io.StringIO()
	stderr = io.StringIO()
	with capture_output(stdout, stderr):
		result = safe_exec(script, globals)
	result = result[0][OUT_VAR_NAME]
	if isinstance(result, str):
		return result

	assert isinstance(result, list), "typecheck"
	if not all(isinstance(r, str) for r in result):
		raise ValueError(f"get_context must return a string or a list of strings got {result}")

	return result


def get_script_and_globals(
	script: str,
	args_def: list[ArgDefinition],
	args: Args,
	function_name: str = "main",
):
	from flow.flow.doctype.fl_settings.fl_settings import get_variables

	globals = {"_print_": RegularPrint, "env": get_variables()}
	if not args_def:
		script = "\n".join([script, f"{OUT_VAR_NAME} = {function_name}()"])
		return script, globals

	arg_list = []
	for ad in args_def:
		"""
		Validation for when default value is not provided should be handled
		before execute is called in FL Script Task itself.
		"""

		arg_name = ad["name"]
		if arg_name not in args:
			continue

		arg_variable_name = f"fl___script_arg_{arg_name}"

		globals[arg_variable_name] = args[arg_name]
		arg_list.append(f"{arg_name}={arg_variable_name}")

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

		# Check if imports are used
		elif isinstance(node, ast.Import | ast.ImportFrom):
			invalidation_reasons.append(f"Imports are not allowed (line: {node.lineno})")

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

Args = dict[str, Any]


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
