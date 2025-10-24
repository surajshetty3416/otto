from __future__ import annotations

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
# import frappe
import io
import json
import time
from typing import TYPE_CHECKING, Any, cast

import frappe
from frappe.exceptions import ValidationError
from frappe.model.document import Document
from frappe.model.naming import make_autoname

import otto
from otto.llm.utils import reset_user
from otto.otto.doctype.otto_task.tools import is_meta_tool
from otto.otto.doctype.otto_tool import lib
from otto.utils import execute

if TYPE_CHECKING:
	from collections.abc import Callable

	from otto.lib.types import ToolSchema, ToolUseUpdate

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
		code: DF.Code | None
		description: DF.LongText | None
		is_external: DF.Check
		is_valid: DF.Check
		mock_return_value: DF.Data | None
		mock_tool: DF.Check
		reason: DF.SmallText | None
		requires_permission: DF.Check
		slug: DF.Data
		title: DF.Data | None
		use_explanation: DF.Check
	# end: auto-generated types

	@staticmethod
	def new(
		*,
		# Labels
		name: str | None = None,
		title: str | None = None,
		# Flags
		is_external: bool = False,
		use_explanation: bool = False,
		requires_permission: bool = False,
		# Mocks
		mock_tool: bool = False,
		mock_return_value: str | None = None,
		# Schema
		schema: ToolSchema | None = None,
		code: str | None = None,
		# Not required if schema is provided
		slug: str | None = None,
		args: list[dict] | None = None,
		description: str | None = None,
	):
		doc = cast("OttoTool", frappe.new_doc("Otto Tool"))
		doc.name = name or make_autoname("hash")
		doc.title = title
		doc.slug = slug or to_slug(title or "")

		doc.description = description
		for arg in args or []:
			doc.append("args", arg)

		if schema:
			doc.set_from_schema(schema)

		doc.is_external = is_external
		if not is_external:
			doc.code = code
			doc.mock_tool = mock_tool
			doc.mock_return_value = mock_return_value

		doc.use_explanation = use_explanation
		doc.requires_permission = requires_permission

		assert doc.slug, "slug is required"
		doc.save()
		return doc

	def validate(self):
		if self.slug and is_meta_tool(self.slug):
			raise frappe.ValidationError(f'Slug cannot be named "{self.slug}" as it is a meta tool')

	def before_save(self):
		self.set_title_or_slug()
		if self.is_external:
			self.validate_external()
			return None

		if not self.code:
			self.set_reason("Code is required")
			return None

		reasons, args_def = execute.validate(self.code, self.slug)
		if reasons:
			return self.set_reason("\n".join(reasons))

		self.is_valid = True
		self.reason = None

		self.set_args(args_def)
		self.validate_arg_types()
		self.validate_descriptions()
		return None

	def validate_external(self):
		self.is_valid = True
		self.reason = None
		self.validate_arg_types()
		self.validate_descriptions()

	def set_title_or_slug(self):
		if self.title and not self.slug:
			parts = [w.lower() for w in self.title.split() if w.isalpha()]
			self.slug = "_".join(parts)

		if self.slug and not self.title:
			parts = [w.capitalize() for w in self.slug.split("_")]
			self.title = " ".join(parts)

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
			self.set_reason("Tool description missing")

		for arg in self.args:
			if arg.description:
				continue

			self.set_reason(f"Description missing for argument: {arg.arg_name}")

	def set_reason(self, reason: str):
		self.reason = self.reason or ""
		self.reason = "\n".join([*self.reason.splitlines(), reason])
		self.is_valid = False

	@frappe.whitelist()
	def get_function_schema(self, slug: str | None = None) -> ToolSchema:
		"""Returns function schema for the tool, add meta properties that might aid in usage reasoning."""

		from otto.llm.types import ToolSchema, ToolSchemaParameters

		properties = {
			arg.arg_name: {"type": arg.type, "description": arg.description or ""} for arg in self.args
		}
		required = [arg.arg_name for arg in self.args if arg.is_required]

		if self.use_explanation:
			properties = {
				"explanation": {
					"type": "string",
					"description": "A short explanation of why the this tool is being called, and how it contributes to the task.",
				},
				**properties,
			}
			required = ["explanation", *required]

		return ToolSchema(
			name=slug or self.slug,
			description=self.description or "",
			parameters=ToolSchemaParameters(
				type="object",
				properties=properties,
				required=required,
			),
		)

	def mock(
		self,
		args: dict[str, Any],
		*,
		chat: str | None = None,
		task: str | None = None,
		session: str | None = None,
	):
		lib.log(
			args,
			tool=self.name,
			chat=chat,
			task=task,
			session=session,
		)

		return execute.SessionResult(
			result=json.loads(self.mock_return_value or "null"),
			stdout="",
			stderr="",
		)

	@reset_user()
	def execute(
		self,
		args: dict[str, Any],
		*,
		force: bool = False,
		chat: str | None = None,
		task: str | None = None,
		session: str | None = None,
		env: dict | None = None,
		fn: Callable | None = None,
	):
		"""Execute tool with given args.
		- force: bypass validation
		- task: task document name (for logging if needed)
		- session: session document name (for logging if needed)
		"""
		if self.is_external and not fn:
			raise ValidationError("External tools must be executed with a function")

		if self.mock_tool:
			return self.mock(args, task=task, session=session, chat=chat)

		if not self.is_valid and not force:
			raise ValidationError("tool is invalid: " + (self.reason or ""))

		if self.is_external:
			assert fn is not None, "type check"
			return self._execute_external(args, fn)

		arg_names = []
		for arg in self.args:
			assert arg.arg_name is not None, "sanity check"
			arg_names.append(arg.arg_name)

		refs = frappe._dict(
			{
				"tool": self.name,
				"task": task,
				"chat": chat,
				"session": session,
			}
		)
		globals = dict(otto=lib.get_lib(env), refs=refs)
		assert self.code is not None, "sanity check"
		return execute.execute(
			self.code,
			args=args,
			arg_names=arg_names,
			globals=globals,
		)

	def _execute_external(self, args: dict[str, Any], fn: Callable):
		stdout = io.StringIO()
		stderr = io.StringIO()
		with execute.capture_output(stdout, stderr):
			result = fn(**args)

		return execute.SessionResult(
			result=result,
			stdout=stdout.getvalue(),
			stderr=stderr.getvalue(),
		)

	@frappe.whitelist()
	def test_tool(self, args: dict[str, Any]):
		result = dict(self.execute(args, force=True))
		if not result["stdout"]:
			del result["stdout"]

		if not result["stderr"]:
			del result["stderr"]

		return json.dumps(result, indent=2)

	def set_from_schema(self, schema: ToolSchema):
		self.slug = schema["name"]
		self.description = schema["description"]
		self.args = []

		for arg in schema["parameters"]["properties"]:
			arg_def = {
				"arg_name": arg,
				"type": schema["parameters"]["properties"].get(arg, {}).get("type", "unknown"),
				"description": schema["parameters"]["properties"].get(arg, {}).get("description", ""),
				"is_required": arg in schema["parameters"]["required"],
			}
			self.append("args", arg_def)


def to_slug(value: str) -> str:
	out = []
	for c in value:
		if c.isalnum():
			out.append(c)
		elif c in (" ", "-", "."):
			out.append("_")
	slug = "".join(out)

	slug = "_".join(part for part in slug.split("_") if part)
	return slug.lower()


def execute_tool(
	*,
	tool: str,
	args: dict,
	tool_use_id: str,
	env_str: str | None,
	task: str | None = None,
	session: str | None = None,
	chat: str | None = None,
	permission_granted: bool,
	denied_reason: str | None = None,
	doc: Document | None = None,
	fn: Callable | None = None,
) -> ToolUseUpdate:
	"""
	Executes a tool and returns a ToolUseUpdate.

	Arguments:
	- tool: ID of the Otto Tool doc to execute
	- args: LLM generated arguments dictionary for the tool.
	- tool_use_id: LLM provider given Tool use ID.
	- env_str: JSON string of environment variables, or None.
	- task: Otto Task doc name (if any)
	- session: Otto Session doc name (if any)
	- chat: Otto Chat doc name (if any)
	- permission_granted: Whether permission to use the tool was granted.
	- denied_reason: Reason for denial, if permission is denied.
	- doc: Otto Execution doc used for error logging (for reference purpose only).
	- fn: Function to execute the tool, if the tool is external.
	"""

	from otto.lib.types import ToolUseUpdate
	from otto.otto.doctype.otto_tool.otto_tool import OttoTool

	update = ToolUseUpdate(id=tool_use_id, start_time=time.time(), end_time=time.time())
	if not permission_granted:
		update["is_error"] = True
		update["result"] = denied_reason or "Permission to use tool denied by user"
		return update

	tool_doc = otto.get(OttoTool, tool)
	try:
		env = json.loads(env_str) if env_str else None
		result = tool_doc.execute(
			args,
			task=task,
			session=session,
			env=env,
			chat=chat,
			fn=fn,
		)
		update["is_error"] = False
		update["result"] = result["result"]
		update["stdout"] = result["stdout"]
		update["stderr"] = result["stderr"]
	except Exception as e:
		otto.log_error(
			"Tool Use Error",
			doc=doc or tool_doc,
			tool=tool,
		)
		update["is_error"] = True
		update["result"] = str(e)
	finally:
		update["end_time"] = time.time()
	return update
