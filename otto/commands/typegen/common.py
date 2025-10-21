import ast
import contextlib
import re
from collections import OrderedDict
from pathlib import Path
from typing import TypeGuard

import click

from otto.commands.typegen.pydantic import get_pydantic_types

FALLBACK_TYPE = "unknown"
OPTIONAL_ARG = "<OPTIONAL>"

# This tag is applied only to dependent types when the FOUND_TYPES set is being
# generated. Once it's generated, the refs are used to populate the USED_TYPES
# set.
REF_START = "<ref:"
REF_END = ":ref>"

TYPE_MAP = {
	"str": "string",
	"int": "number",
	"float": "number",
	"bool": "boolean",
	"list": f"{FALLBACK_TYPE}[]",
	"dict": f"Record<string, {FALLBACK_TYPE}>",
	"tuple": f"{FALLBACK_TYPE}[]",
	"Any": "unknown",
	"None": "null",
}

TypeScriptType = str

# Set to track Type symbols that are found in the codebase
FOUND_TYPES: set[str] = set()
USED_TYPES: set[str] = set()

FoundTypes = OrderedDict[str, tuple[Path, str]]

is_populating_found_types = False


def populate_found_types(root: Path) -> FoundTypes:
	"""Populate the FOUND_TYPES set with all the Type symbols in the codebase"""
	print("Finding types...")

	found_types: FoundTypes = OrderedDict()
	global is_populating_found_types

	is_populating_found_types = True
	for filepath in root.glob("**/*.py"):
		pyd_types = get_pydantic_types(filepath.as_posix())
		for key, type_str in format_pyd_types(pyd_types).items():
			found_types[key] = (filepath, type_str)
			FOUND_TYPES.add(key)

		found_types.update(populate_found_types_for_file(filepath))
	is_populating_found_types = False
	print(f"Found {click.style(len(FOUND_TYPES), fg='yellow')} types\n")

	return found_types


def format_pyd_types(pyd_types: dict[str, str]) -> dict[str, str]:
	"""Format the pydantic type_str to use refs for later substituted"""
	formatted_types = {}
	for type_name, type_def in pyd_types.items():
		formatted_def = type_def

		# Replace references to other types with the REF format
		for k in pyd_types:
			if k == type_name:
				continue

			# Use word boundaries to ensure we're replacing the full type name
			pattern = rf"\b{re.escape(k)}\b"
			replacement = f"{REF_START}{k}{REF_END}"
			formatted_def = re.sub(pattern, replacement, formatted_def)
		formatted_types[type_name] = formatted_def
	return formatted_types


def populate_found_types_for_file(filepath: Path):
	with filepath.open("r") as f:
		content = f.read()

	tree = ast.parse(content)
	found_types: OrderedDict[str, tuple[Path, str]] = OrderedDict()

	for node in ast.walk(tree):
		# Node has already been found
		if hasattr(node, "name") and getattr(node, "name", "") in FOUND_TYPES:
			continue

		# TypedDict classes
		if is_typed_dict(node):
			found_types[node.name] = (filepath, handle_typed_dict(node))
			FOUND_TYPES.add(node.name)
			continue

		# Handle type aliases like Status = Literal['Success', 'Failure'] or Name = str
		if (isinstance(node, ast.Assign) and len(node.targets) == 1) or isinstance(node, ast.TypeAlias):
			if isinstance(node, ast.TypeAlias):
				target = node.name
			else:
				target = node.targets[0]

			if not isinstance(target, ast.Name) or (type_name := target.id) in FOUND_TYPES:
				continue

			# All types should be uppercase
			if not type_name[0].isupper():
				continue

			is_primitive = isinstance(node.value, ast.Constant) and isinstance(
				node.value.value, str | int | float | bool
			)

			# Skip if it's not a type annotation or not a primitive literal
			if not is_primitive and not isinstance(
				node.value, ast.Name | ast.Subscript | ast.Attribute | ast.BinOp | ast.Call
			):
				continue

			FOUND_TYPES.add(type_name)
			ts_type = get_typescript_type(node.value)
			found_types[type_name] = (filepath, f"export type {type_name} = {ts_type};")

	return found_types


def get_type_name(node: ast.AST) -> str | None:
	if is_typed_dict(node):
		return node.name

	if isinstance(node, ast.ClassDef):  # probably Pydantic type
		return node.name

	if not isinstance(node, ast.Assign) or len(node.targets) != 1:
		return None

	target = node.targets[0]
	if not isinstance(target, ast.Name):
		return None

	return target.id


def is_typed_dict(node: ast.AST) -> TypeGuard[ast.ClassDef]:
	return isinstance(node, ast.ClassDef) and any(
		isinstance(base, ast.Name) and base.id == "TypedDict" for base in node.bases
	)


def handle_subscript(node: ast.Subscript) -> TypeScriptType:
	"""Recursively convert Python type annotations to TypeScript types.
	Examples:
		list[str] -> string[]
		dict[str, int] -> Record<string, number>
		list[dict[str, str]] -> Record<string, string>[]
		tuple[str] -> string[]
	"""
	value = node.value
	if not isinstance(value, ast.Name):
		return FALLBACK_TYPE

	base_type = value.id
	if base_type not in ("list", "dict"):
		return FALLBACK_TYPE

	# Handle list and tuple type annotations
	if base_type == "list":
		if not isinstance(node.slice, ast.Name) and not isinstance(node.slice, ast.Subscript):
			return FALLBACK_TYPE
		inner_type = get_typescript_type(node.slice)
		return f"{inner_type}[]"

	# Handle dict type annotations
	if base_type == "dict":
		if not isinstance(node.slice, ast.Tuple):
			return FALLBACK_TYPE

		if len(node.slice.elts) != 2:
			return FALLBACK_TYPE

		key_type = get_typescript_type(node.slice.elts[0])
		value_type = get_typescript_type(node.slice.elts[1])

		# JS objects only have strings or symbols as keys
		if key_type != "string":
			print(
				f"Found non-string key type {click.style(key_type, fg='yellow')} for {click.style(ast.unparse(node), fg='blue')}"
			)

		return f"Record<string, {value_type}>"
	return FALLBACK_TYPE


def handle_literal(annotation: ast.Subscript) -> TypeScriptType:
	def get_primitive_literal(value: ast.expr) -> str:
		if not isinstance(value, ast.Constant):
			return FALLBACK_TYPE

		if isinstance(value.value, str):
			return f'"{value.value}"'

		if value.value is True:
			return "true"

		if value.value is False:
			return "false"

		return str(value.value)

	# Multiple literal values
	if isinstance(annotation.slice, ast.Tuple):
		values = []
		for elt in annotation.slice.elts:
			values.append(get_primitive_literal(elt))
		return " | ".join(values)

	# Single literal value
	if isinstance(annotation.slice, ast.Constant):
		return get_primitive_literal(annotation.slice)

	return handle_subscript(annotation)


def handle_typed_dict(node: ast.ClassDef) -> str:
	"""Convert a TypedDict class to a TypeScript interface"""
	interface_name = node.name
	fields = []

	for item in node.body:
		if not isinstance(item, ast.AnnAssign):
			continue
		if not item.target or not item.annotation:
			continue

		field_name = item.target.id if isinstance(item.target, ast.Name) else str(item.target)
		field_type = get_typescript_type(item.annotation)
		fields.append(f"  {field_name}: {field_type};")

	return f"export interface {interface_name} {{\n" + "\n".join(fields) + "\n}\n"


def get_typescript_type(annotation: ast.expr | None) -> TypeScriptType:
	"""
	Note here we cannot convert all Python types to TypeScript types.
	- Types that don't have an equivalent in TypeScript are not supported (eg: tuple)

	The expectation here is to keep the APIs as simple as possible and to have
	some reasonable amount of completion on the frontend. It is unreasonable to
	try and convert all possible Python types to TypeScript types.
	"""
	if annotation is None:
		return FALLBACK_TYPE

	if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
		with contextlib.suppress(Exception):
			stmt = ast.parse(annotation.value).body[0]
			if isinstance(stmt, ast.Expr):
				stmt = stmt.value
			if isinstance(stmt, ast.Name):
				annotation = stmt

	if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
		# Handle union types (e.g., str | None)
		left_type = get_typescript_type(annotation.left)
		right_type = get_typescript_type(annotation.right)
		types = [left_type, right_type]
		return " | ".join(types)

	if isinstance(annotation, ast.Name):
		# Type might have a not yet found reference
		if is_populating_found_types and annotation.id not in TYPE_MAP:
			return f"{REF_START}{annotation.id}{REF_END}"

		if not is_populating_found_types and annotation.id in FOUND_TYPES:
			USED_TYPES.add(annotation.id)
			return annotation.id

		return TYPE_MAP.get(annotation.id, FALLBACK_TYPE)

	if isinstance(annotation, ast.Constant):
		if annotation.value is None:
			return "null"
		if isinstance(annotation.value, str):
			return TYPE_MAP.get(annotation.value, FALLBACK_TYPE)

	if isinstance(annotation, ast.Subscript):
		# Handle Literal types
		if isinstance(annotation.value, ast.Name) and annotation.value.id == "Literal":
			return handle_literal(annotation)
		return handle_subscript(annotation)

	if not is_populating_found_types:
		print(
			f"{click.style('*', fg='red')} Found complex type {click.style(ast.unparse(annotation), fg='yellow')} ({click.style(annotation, fg='blue')})"
		)
	return FALLBACK_TYPE


def replace_ref_types(type_str: str) -> str:
	"""Replace reference placeholders with actual type names if found, or fallback type if not."""
	while REF_START in type_str and REF_END in type_str:
		start_idx = type_str.find(REF_START)
		end_idx = type_str.find(REF_END, start_idx)

		if start_idx == -1 or end_idx == -1:
			break

		ref_id = type_str[start_idx + len(REF_START) : end_idx]

		replacement = FALLBACK_TYPE
		if ref_id in FOUND_TYPES:
			replacement = ref_id
			USED_TYPES.add(ref_id)

		type_str = type_str[:start_idx] + replacement + type_str[end_idx + len(REF_END) :]

	return type_str


def get_dependent_types(relative_root: Path, found_types: FoundTypes, content: str) -> list[str]:
	"""Get dependent types from the codebase as a list that is to be newline joined"""
	used_types = []
	added_types = set()

	while len(USED_TYPES) > 0:
		name = USED_TYPES.pop()

		if name in added_types:
			continue

		if (ft := found_types.get(name)) is None:
			continue

		if is_defined(name, content):
			print(click.style(f"Type {name} already defined", fg="yellow"))
			continue

		(type_path, type_str) = ft
		type_str = replace_ref_types(type_str)
		used_types.append(f"// {type_path.relative_to(relative_root)}")
		used_types.append(type_str)
		used_types.append("")

	return used_types


def is_defined(type_name: str, content: str) -> bool:
	return f"interface {type_name}" in content or f"type {type_name}" in content
