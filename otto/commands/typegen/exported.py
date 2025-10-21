import ast
from pathlib import Path

import click
from frappe import get_app_path

from otto.commands.typegen.common import (
	FoundTypes,
	get_dependent_types,
	get_type_name,
	is_defined,
	replace_ref_types,
)
from otto.commands.typegen.utils import clear_types, get_out_path, save_types
from otto.commands.utils import get_bench_root

EXPORT_TAG = " ".join(["#", "@export"])


def get_exported_types(found_types: FoundTypes, out_path: Path):
	if not (bench_root := get_bench_root()):
		print(click.style("Bench root not found", fg="red"))
		return None

	app_path = Path(get_app_path("otto"))
	if not app_path.exists():
		print(click.style("App path not found", fg="red"))
		return None

	type_names = []
	for file in app_path.glob("**/*.py"):
		with open(file, "r") as f:
			content = f.read()
			if EXPORT_TAG not in content:
				continue

			print("Exporting from", click.style(file.relative_to(app_path), fg="blue"))
			lines = content.splitlines()

			# Parse the file to find exported types
			try:
				tree = ast.parse(content)
				type_names.extend(
					extract_exported_type_names(
						tree,
						lines,
					)
				)
			except SyntaxError as e:
				print(click.style(f"Syntax error in {file}: {e}", fg="red"))

	if not type_names:
		return None

	with out_path.open("r") as f:
		content = f.read()

	exported_types = []
	relative_root = bench_root / "apps"

	for type_name in type_names:
		if is_defined(type_name, content):
			print(click.style(f"Type {type_name} already defined", fg="yellow"))
			continue

		type_path, type_str = found_types[type_name]
		type_str = replace_ref_types(type_str)
		exported_types.append(f"// {type_path.relative_to(relative_root)}")
		exported_types.append(type_str)
		exported_types.append("")

	dependent_types = get_dependent_types(relative_root, found_types, content)

	return "\n".join([*dependent_types, *exported_types])


def extract_exported_type_names(
	tree: ast.AST,
	lines: list[str],
) -> list[str]:
	"""Extract types marked with @export and convert them to TypeScript"""
	type_names = []
	for node in ast.walk(tree):
		# Look for classes with @export in docstring or comment
		if not is_exported(node, lines):
			continue

		type_name = get_type_name(node)
		if type_name is None:
			ref = getattr(node, "name", "") or getattr(node, "id", "") or ast.unparse(node)
			print(click.style(f"Could not extract type name for {node} ({ref})", fg="red"))
			continue

		type_names.append(type_name)

	return type_names


def is_exported(node: ast.AST, lines: list[str]) -> bool:
	"""Check if a node has an @export comment"""
	lineno = getattr(node, "lineno", None)
	if lineno is None or lineno > len(lines):
		return False

	if not lines[lineno - 2].strip().startswith(EXPORT_TAG):
		return False

	return not isinstance(node, ast.Name)


def generate_exported_types(out: str, found_types: FoundTypes):
	print(click.style("Generating Exported Types", fg="magenta"))

	app = "otto"
	if not (out_path := get_out_path(app, out)):
		return False

	app_name = app.capitalize()
	tag = f"Exported Types for {app_name}"
	clear_types(tag, out_path)

	if not (exported_types := get_exported_types(found_types, out_path)):
		return False

	return save_types(
		types=exported_types,
		tag=tag,
		out_path=out_path,
	)
