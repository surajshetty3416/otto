import ast
from pathlib import Path
from typing import NamedTuple

import click

from otto.commands.typegen.common import (
	OPTIONAL_ARG,
	FoundTypes,
	TypeScriptType,
	get_dependent_types,
	get_typescript_type,
)
from otto.commands.typegen.utils import clear_types, get_out_path, save_types
from otto.commands.utils import get_bench_root


class Param(NamedTuple):
	name: str
	type: TypeScriptType


class APIFunction(NamedTuple):
	name: str
	params: list[Param]
	return_type: TypeScriptType | None
	allow_guest: bool
	filepath: Path


def is_whitelist_decorator(node: ast.Call) -> tuple[bool, bool]:
	"""Check if a node is a frappe.whitelist decorator and if it allows guests"""
	if not isinstance(node.func, ast.Attribute):
		return False, False

	if (
		node.func.attr == "whitelist"
		and isinstance(node.func.value, ast.Name)
		and node.func.value.id == "frappe"
	):
		allow_guest = False
		for keyword in node.keywords:
			if keyword.arg == "allow_guest" and isinstance(keyword.value, ast.Constant):
				allow_guest = bool(keyword.value.value)
		return True, allow_guest
	return False, False


def extract_function_info(node: ast.FunctionDef, filepath: Path, allow_guest: bool) -> APIFunction:
	"""Extract function signature information from an AST node"""
	params = []
	min_default_index = len(node.args.args) - len(node.args.defaults)

	for i, arg in enumerate(node.args.args):
		param_type = get_typescript_type(arg.annotation)
		# If argument has a default value, make it optional
		if i >= min_default_index:
			param_type += OPTIONAL_ARG
		param_info = Param(name=arg.arg, type=param_type)
		params.append(param_info)

	if not node.returns:
		print(f"{click.style('*', fg='red')} No return type for {click.style(node.name, fg='blue')}")

	return_type = get_typescript_type(node.returns)

	return APIFunction(
		name=node.name,
		params=params,
		return_type=return_type,
		allow_guest=allow_guest,
		filepath=filepath,
	)


def find_api_functions(filepath: Path) -> list[APIFunction]:
	"""Find all whitelisted functions in a Python file"""
	with filepath.open("r") as f:
		content = f.read()

	try:
		tree = ast.parse(content)
	except SyntaxError as e:
		print(click.style(f"Syntax error in {filepath}: {e}", fg="red"))
		return []

	api_functions = []
	for node in ast.walk(tree):
		if not isinstance(node, ast.FunctionDef):
			continue

		for decorator in node.decorator_list:
			if not isinstance(decorator, ast.Call):
				continue

			is_whitelist, allow_guest = is_whitelist_decorator(decorator)
			if not is_whitelist:
				continue

			print(f"Extracting types for {click.style(node.name, fg='blue')}")
			api_function = extract_function_info(node, filepath, allow_guest)
			api_functions.append(api_function)

	return api_functions


def get_type_obj(api_path: Path, all_api_functions: list[APIFunction]):
	type_obj = {}
	for func in all_api_functions:
		func_str = get_func_str(func)
		filepath = func.filepath.relative_to(api_path)

		prev_type_obj = type_obj
		for part in filepath.parts:
			if not part.endswith(".py"):
				prev_type_obj = prev_type_obj.setdefault(part, {})
				continue

			if part.endswith(".py"):
				part = part[:-3]

			if part != "__init__":
				prev_type_obj = prev_type_obj.setdefault(part, {})

			prev_type_obj[func.name] = func_str

	return type_obj


def get_func_str(func: APIFunction):
	params = []
	for p in func.params:
		# If type ends with " | undefined", make it optional with ?
		if p.type.endswith(OPTIONAL_ARG):
			base_type = p.type.removesuffix(OPTIONAL_ARG)
			params.append(f"{p.name}?: {base_type}")
		else:
			params.append(f"{p.name}: {p.type}")

	params_str = ""
	if params:
		params_str = f"args: {{{', '.join(params)}}}"

	return_str = f"{func.return_type}"
	return f"{func.name}({params_str}): {return_str};"


def get_ts_interface_from_type_obj(json_obj, interface_name="API"):
	def generate_interface(obj, indent="  "):
		lines = []
		for key, value in obj.items():
			if isinstance(value, str):
				lines.append(f"{indent}{value}")
				continue

			assert isinstance(value, dict), f"Expected dict, got {value} of type {type(value)}"
			nested = generate_interface(value, indent + "  ")
			lines.append(f"{indent}{key}: {{\n{nested}\n{indent}}};")

		return "\n".join(lines)

	# Generate the complete interface
	interface = f"export interface {interface_name} {{\n"
	interface += generate_interface(json_obj)
	interface += "\n}"

	return interface


def get_api_types(found_types: FoundTypes, out_path: Path) -> str | None:
	"""
	Generate API types for all whitelisted functions in an app. Example:

	From:
	```
		api/
		├── __init__.py
		│   ├── def ping() -> Literal["pong"]: ...
		│   └── def echo(message: str) -> str: ...
		└── example.py
			└── def some_function(message: str) -> str: ...
	```

	To:
	```typescript
		export interface API {
			ping(): Call<string>;
			echo(args: {message: string}): Call<string>;
			example: {
				some_function(args: {message: string}): Call<string>;
			}
		}
	```
	"""
	bench_root = get_bench_root()
	if not bench_root:
		return print(click.style("Bench root not found", fg="red"))

	app = "otto"
	app_dir = bench_root / "apps" / app / app
	api_dir = app_dir / "api"
	if not api_dir.exists():
		return print(click.style(f"API directory not found: {api_dir}", fg="red"))

	all_api_functions = []
	# Collect all API functions
	for filepath in api_dir.glob("**/*.py"):
		api_functions = find_api_functions(filepath)
		all_api_functions.extend(api_functions)

	if not all_api_functions:
		print(click.style("No API functions found", fg="yellow"))

	type_obj = get_type_obj(api_dir, all_api_functions)
	api_interface = get_ts_interface_from_type_obj(type_obj)

	with out_path.open("r") as f:
		content = f.read()

	# Combine TypedDict interfaces with API interface
	dependent_types = get_dependent_types(bench_root / "apps", found_types, content)

	return "\n".join([*dependent_types, api_interface])


def generate_api_types(out: str, found_types: FoundTypes):
	print(click.style("Generating API types", fg="magenta"))
	app = "otto"
	if not (out_path := get_out_path(app, out)):
		return False

	app_name = app.capitalize()
	tag = f"API Types for {app_name}"
	clear_types(tag, out_path)

	if not (api_types := get_api_types(found_types, out_path)):
		return False

	return save_types(
		types=api_types,
		tag=tag,
		out_path=out_path,
	)
