from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
# import frappe
import json
import textwrap
from typing import Any

import frappe
from frappe.exceptions import ValidationError
from frappe.model.document import Document

from otto.otto.doctype.otto_tool import lib
from otto.utils import execute, json_dumps

arg_type_to_json_type = {
	"str": "string",
	"int": "integer",
	"float": "number",
	"bool": "boolean",
	"list": "array",
	"dict": "object",
}


class OttoTool(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_tool_arg_ct.otto_tool_arg_ct import OttoToolArgCT

		args: DF.Table[OttoToolArgCT]
		code: DF.Code
		description: DF.LongText | None
		is_valid: DF.Check
		reason: DF.SmallText | None
		slug: DF.Data
		mock_tool: DF.Check
		mock_return_value: DF.Data | None
	# end: auto-generated types

	@staticmethod
	def new(
		slug: str,
		description: str,
		code: str,
		*,
		args: list[dict] | None = None,
		mock_tool: bool = False,
		mock_return_value: str | None = None,
	):
		doc = frappe.get_doc(
			{
				"doctype": "Otto Tool",
				"slug": slug,
				"description": description,
				"code": code,
				"mock_tool": mock_tool,
				"mock_return_value": mock_return_value,
			}
		)

		for arg in args or []:
			doc.append("args", arg)

		doc.save()
		return doc

	def before_save(self):
		reasons, args_def = execute.validate(self.code, self.slug)
		if reasons:
			return self.set_reason("\n".join(reasons))

		self.is_valid = True
		self.reason = None

		self.set_args(args_def)
		self.validate_arg_types()
		self.validate_descriptions()

	def set_args(self, args_def: list[execute.ArgDefinition]):
		prev_meta = {a.arg_name: (a.type, a.description) for a in (self.args or [])}

		# Reset to prevent dupes
		self.args = []
		for arg in args_def:
			arg_type = arg_type_to_json_type.get(arg["type"], "unknown")

			if arg_type == "unknown":
				arg_type = prev_meta.get(arg["name"], ("unknown", ""))[0]

			if arg_type == "unknown":
				self.set_reason(f"Could not infer JSON type for argument: {arg['name']}")

			self.append(
				"args",
				{
					"arg_name": arg["name"],
					"type": arg_type,
					"description": prev_meta.get(arg["name"], ("", ""))[1],
					"is_required": not arg["has_default"],
				},
			)

	def validate_arg_types(self):
		valid_types = ["string", "integer", "number", "boolean", "array", "object"]
		for arg in self.args:
			if arg.type in valid_types:
				continue

			self.set_reason(
				f"Invalid JSON type for {arg.arg_name}: {arg.type}, please specify valid type from {valid_types}"
			)

	def validate_descriptions(self):
		if not self.description:
			self.is_valid = False
			self.set_reason("Tool description missing")

		for arg in self.args:
			if arg.description:
				continue

			self.set_reason(f"Description missing for argument: {arg.arg_name}")

	def set_reason(self, reason: str):
		self.reason = self.reason or ""
		self.reason = "\n".join(self.reason.splitlines() + [reason])
		self.is_valid = False

	@frappe.whitelist()
	def get_function_schema(self):
		"""Returns function schema for the tool, add meta properties that might aid in usage reasoning."""
		properties = {
			arg.arg_name: {"type": arg.type, "description": arg.description or ""} for arg in self.args
		}

		"""Returns tool as a JSON Schema function"""
		schema = {
			"name": self.slug,
			"description": self.description or "",
			"parameters": {
				"type": "object",
				"properties": {
					"explanation": {
						"type": "string",
						"description": "A short explanation of why the this tool is being called, and how it contributes to the task.",
					},
					**properties,
				},
				"required": ["explanation"] + [arg.arg_name for arg in self.args if arg.is_required],
			},
		}

		return {
			"type": "function",
			"function": schema,
		}

	def mock(
		self,
		args: dict[str, Any],
		*,
		task: str | None = None,
		execution: str | None = None,
	):
		content = ""
		for k, v in args.items():
			content += f"{k}:\n"
			if not isinstance(v, str):
				v, _ = json_dumps(v)
			content += textwrap.indent(v, "    ")
			content += "\n\n"
		content = content.strip()

		lib.log(content, tool=self.name, task=task, execution=execution)
		return execute.ExecutionResult(
			result=json.loads(self.mock_return_value or "null"),
			stdout="",
			stderr="",
		)

	def execute(
		self,
		args: dict[str, Any],
		*,
		force: bool = False,
		task: str | None = None,
		execution: str | None = None,
	):
		"""Execute tool with given args.
		- force: bypass validation
		- task: task document name (for logging if needed)
		- execution: execution document name (for logging if needed)
		"""
		if self.mock_tool:
			return self.mock(args, task=task, execution=execution)

		if not self.is_valid and not force:
			raise ValidationError("tool is invalid: " + (self.reason or ""))

		arg_names = []
		for arg in self.args:
			assert arg.arg_name is not None, "sanity check"
			arg_names.append(arg.arg_name)

		refs = frappe._dict(
			{
				"tool": self.name,
				"task": task,
				"execution": execution,
			}
		)
		globals = dict(otto=lib.get_lib(), refs=refs)

		return execute.execute(
			self.code,
			args=args,
			arg_names=arg_names,
			globals=globals,
		)

	@frappe.whitelist()
	def test_execute(self, args: dict[str, Any]):
		try:
			result = dict(self.execute(args, force=True))
			if not result["stdout"]:
				del result["stdout"]

			if not result["stderr"]:
				del result["stderr"]

			return json.dumps(result, indent=2)
		except Exception as e:
			return f"error: {e}"
