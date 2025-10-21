import json
import os
from pathlib import Path
from typing import Any

import click

from otto.commands.typegen.utils import get_out_path, save_types
from otto.commands.utils import get_bench_root

"""Maps Frappe fieldtypes to TypeScript types"""
type_mapping = {
	"Data": "string",
	"Code": "string",
	"Text": "string",
	"Link": "string",
	"Dynamic Link": "string",
	"Small Text": "string",
	"Long Text": "string",
	"Markdown Editor": "string",
	"Text Editor": "string",
	"Check": "number | boolean",
	"Int": "number",
	"Float": "number",
	"Currency": "number",
	"Percent": "number",
	"JSON": "string",
	"Date": "string",
	"Datetime": "string",
	"Time": "string",
	# Indirect fieldtypes
	"Table": "",
	"Select": "",
	# Non Data Types, mentioned for completeness
	"Section Break": "",
	"Column Break": "",
}


def generate_interface_fields(name: str, fields: list[dict[str, Any]]) -> list[str]:
	"""Generates TypeScript interface field definitions from DocType fields"""
	interface_fields = []

	for field in fields:
		# Skip break fields as they're UI-only
		if field["fieldtype"] in ["Section Break", "Column Break"]:
			continue

		fieldname = field["fieldname"]
		fieldtype = field["fieldtype"]

		if fieldtype not in type_mapping:
			print(
				click.style(
					f"Warning: mapping not found for fieldname {fieldname} of fieldtype {fieldtype} in {name}",
					fg="yellow",
				)
			)
			continue

		ts_fieldtype = type_mapping[fieldtype]
		if fieldtype == "Table":
			ct_doctype = field["options"].replace(" ", "")
			ts_fieldtype = f"{ct_doctype}[]"

		if fieldtype == "Select":
			options = [f'"{o}"' for o in field["options"].split("\n")]
			ts_fieldtype = " | ".join(options)

		# Add optional modifier (?) if field is not required
		is_required = field.get("reqd", 0) == 1
		modifier = "" if is_required else "?"

		interface_fields.append(f"{fieldname}{modifier}: {ts_fieldtype};")

	return interface_fields


def generate_interface(dir_name: str, schema_path: Path) -> tuple[str, str, str] | tuple[None, None, None]:
	"""Generates a complete TypeScript interface for a DocType"""

	print(f"Generating types for {click.style(dir_name, fg='blue')}")
	with open(schema_path, "r") as f:
		schema = json.load(f)

	doctype_name = schema.get("name")
	interface_name = doctype_name.replace(" ", "")
	if not interface_name:
		print(click.style(f"Warning: No name found for {dir_name}", fg="yellow"))
		return None, None, None

	field_definitions = generate_interface_fields(interface_name, schema["fields"])
	interface = [
		f'export interface {interface_name} extends BaseDoc<"{doctype_name}"> {{',
		*[f"  {fd}" for fd in field_definitions],
		"}",
	]

	return doctype_name, interface_name, "\n".join(interface)


def get_doctype_types(app: str) -> str | None:
	"""Use DocType JSON schemas to generate TypeScript interfaces"""
	if not (bench_root := get_bench_root()):
		return print(click.style(f"Error: Bench root not found from {os.getcwd()}", fg="red"))

	app_dir = bench_root / "apps" / app
	doctypes_dir = app_dir / app / app / "doctype"
	if not doctypes_dir.exists():
		return print(click.style(f"Warning: DocType directory not found at {doctypes_dir}", fg="yellow"))

	names = []
	interfaces = []
	# Iterate through all subdirectories in the doctype folder
	for doctype_path in doctypes_dir.iterdir():
		if not doctype_path.is_dir() or doctype_path.name.startswith("__"):
			continue

		schema_path = doctype_path / f"{doctype_path.name}.json"
		if not schema_path.exists():
			print(
				click.style(
					f"Warning: Schema for {doctype_path.name} not found at {schema_path}", fg="yellow"
				)
			)
			continue

		doctype_name, interface_name, interface = generate_interface(doctype_path.name, schema_path)
		if not doctype_name or not interface_name or not interface:
			continue

		names.append((doctype_name, interface_name))
		interfaces.append(interface)

	# Create a DocType interface that includes all the interfaces
	dt_interface = [
		f"export interface {app.capitalize()}DocTypes {{",
		*[f'  "{d}": {i};' for d, i in names],
		"}",
	]
	interfaces.append("\n".join(dt_interface))

	return "\n\n".join(interfaces)


def generate_doctype_types(app: str, out: str) -> bool:
	print(click.style("Generating DocType types", fg="magenta"))
	if not (dt_types := get_doctype_types(app)):
		print(click.style("Error: DocType types could not be generated", fg="red"))
		return False

	if not (out_path := get_out_path(app, out)):
		return False

	app_name = app.capitalize()
	return save_types(
		types=dt_types,
		tag=f"DocType Types for {app_name}",
		out_path=out_path,
	)
