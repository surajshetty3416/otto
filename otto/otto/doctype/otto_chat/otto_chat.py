from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, cast, overload

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

import otto
import otto.lib as lib
from otto.llm.utils import DEFAULT_MODEL
from otto.otto.doctype.otto_permission_request.otto_permission_request import (
	OttoPermissionRequest,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from otto.lib.types import PendingToolUse, Query, ReasoningEffort, ToolUseUpdate
	from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant
	from otto.otto.doctype.otto_permission_request.otto_permission_request import RequestStatus


class ToolConfig(TypedDict):
	title: str
	slug: str
	tool: str  # Otto Tool name
	is_external: bool
	requires_permission: bool
	is_valid: bool
	reason: str | None
	use_explanation: bool
	is_readonly: bool


class OttoChat(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_chat_tool_ct.otto_chat_tool_ct import OttoChatToolCT

		assistant: DF.Link
		llm: DF.Link | None
		reasoning_effort: DF.Literal["Default", "None", "Low", "Medium", "High"]
		session: DF.Link
		title: DF.Data | None
		tool_permissions: DF.Literal[
			"Default", "Allow All", "Allow Readonly", "Ask For All", "Ask For Non Readonly"
		]
		tools: DF.Table[OttoChatToolCT]
		user_directives: DF.Code | None
	# end: auto-generated types

	_session: lib.Session | None = None
	_assistant: OttoAssistant | None = None
	_pending_tool_use: list[PendingToolUse] | None = None
	_tool_configs: list[ToolConfig] | None = None
	_tool_configs_map: dict[str, ToolConfig] | None = None
	_pending_tools: list[PendingToolUse] | None = None

	@property
	def assistant_(self) -> OttoAssistant:
		from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant

		if not self._assistant:
			self._assistant = otto.get(OttoAssistant, self.assistant)
		return self._assistant

	@property
	def tool_configs(self) -> list[ToolConfig]:
		"""Returns: dict[slug, otto_tool_name]"""
		if self._tool_configs is not None:
			return self._tool_configs

		tool_names = [tool.tool for tool in self.tools]

		tools = {
			t.name: t
			for t in frappe.get_all(
				"Otto Tool",
				filters={"name": ["in", tool_names]},
				fields=[
					"title",
					"name",
					"slug",
					"is_external",
					"use_explanation",
					"is_valid",
					"reason",
					"is_readonly",
				],
			)
		}

		configs: list[ToolConfig] = []
		for tool in self.tools:
			if not tool.slug:
				continue

			td = tools[tool.tool]
			config = ToolConfig(
				slug=tool.slug,
				tool=tool.tool,
				is_external=bool(td.is_external),
				requires_permission=bool(tool.requires_permission),
				title=td.title,
				is_valid=bool(td.is_valid),
				reason=td.reason or None,
				use_explanation=bool(td.use_explanation),
				is_readonly=bool(td.is_readonly),
			)
			configs.append(config)
		self._tool_configs = configs
		return configs

	@property
	def tool_config_map(self) -> dict[str, ToolConfig]:
		if self._tool_configs_map is not None:
			return self._tool_configs_map

		tc_map = {config["slug"]: config for config in self.tool_configs}
		self._tool_configs_map = tc_map
		return tc_map

	def _get_tool_config(self, slug: str) -> ToolConfig:
		config = self.tool_config_map.get(slug)
		assert config is not None, f"Tool config should be set for {slug}"
		return config

	@property
	def session_(self) -> lib.Session:
		if not self._session:
			self._session = lib.load(self.session)
		return self._session

	@session_.setter
	def session_(self, session: lib.Session):
		self._session = session
		self.session = session.id

	@staticmethod
	def new(
		assistant: str,
		*,
		llm: str | None = None,
		reasoning_effort: ReasoningEffort | Literal["Default"] | None = None,
		tool_permissions: Literal[
			"Default",
			"Allow All",
			"Allow Readonly",
			"Ask For All",
			"Ask For Non Readonly",
		]
		| None = None,
		user_directives: str | None = None,
	) -> OttoChat:
		from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		doc = cast("OttoChat", frappe.new_doc("Otto Chat"))
		assistant_doc = otto.get(OttoAssistant, assistant)
		doc.assistant = assistant

		# Chat Settings
		doc.llm = llm
		doc.reasoning_effort = reasoning_effort or "Default"
		doc.tool_permissions = tool_permissions or "Default"
		doc.user_directives = user_directives or ""

		tool_schemas: list[lib.types.ToolSchema] = []
		for tool_ref in assistant_doc.tools:
			if not tool_ref.is_enabled:
				continue

			tool_doc = otto.get(OttoTool, tool_ref.tool)
			schema = tool_doc.get_function_schema(slug=tool_ref.slug)
			tool_schemas.append(schema)

		context = {}
		if user_directives:
			context["user_directives"] = user_directives

		reasoning_effort = assistant_doc.reasoning_effort if doc.reasoning_effort == "Default" else None
		model = llm or assistant_doc.llm or DEFAULT_MODEL
		session = lib.new(
			model=model,
			instruction=assistant_doc.get_instruction(context),
			reasoning_effort=reasoning_effort,
			tools=tool_schemas,
		)
		doc.session_ = session
		doc._copy_tools(assistant_doc)
		doc.title = "New Chat with " + assistant_doc.title

		doc.save()
		return doc

	def autoset_title(self):
		title = generate_session_title(self.session_)
		if not title:
			return False

		self.title = title
		self.save(ignore_permissions=True)
		return True

	def chat(self, query: Query | None = None):
		"""query can be None when resuming after a tool use request"""
		if self.has_pending_requests():
			return None, "Resolve all pending requests before resuming chat"

		self._update_session_tools()
		self._ensure_settings_in_sync()
		self._pending_tools = None
		return self.session_.interact(query, stream=True), None

	def can_resume(self) -> tuple[bool, str | None]:
		"""
		A chat can be resumed only if all pending requests have been resolved,
		all pending tools have been executed and the reason an LLM stopped
		generation was for tool execution.
		"""

		if self.has_pending_requests():
			return False, "Has pending requests"

		if self.get_pending_tools():
			return False, "Has pending tools"

		last_item = self.session_.get_last_item()
		if not last_item:
			return False, "Has no last item"

		if last_item["meta"]["role"] == "user":
			return True, "Last item is a user message"

		if last_item["meta"]["end_reason"] == "turn_end":
			return False, "Assistant has ended the turn"

		assert last_item["meta"]["end_reason"] == "tool_use", "Last item should be a tool use"
		return True, "Last item was a tool use"

	@overload
	def get_pending_requests(self, name_only: Literal[False] = False) -> list[OttoPermissionRequest]: ...

	@overload
	def get_pending_requests(self, name_only: Literal[True]) -> list[str]: ...

	def get_pending_requests(self, name_only: bool = False) -> list[OttoPermissionRequest] | list[str]:
		self._raise_permissions_requests()
		request_names = frappe.get_all(
			"Otto Permission Request",
			filters={
				"session": self.session,
				"status": "Pending",
			},
			pluck="name",
		)

		if name_only:
			return request_names

		return [otto.get(OttoPermissionRequest, req) for req in request_names]

	def has_pending_requests(self) -> bool:
		self._raise_permissions_requests()
		rm = self._get_requests_map()
		return any(status == "Pending" for status in rm.values())

	def _raise_permissions_requests(self) -> list[OttoPermissionRequest]:
		requests: list[OttoPermissionRequest] = []
		pending_tool_use = self.get_pending_tools()
		for ptu in pending_tool_use:
			config = self._get_tool_config(ptu.name)

			should_raise = (
				config["requires_permission"]
				or self.tool_permissions == "Ask For All"
				or (not config["is_readonly"] and self.tool_permissions == "Ask For Non Readonly")
			)

			if not should_raise:
				continue

			if bool(
				frappe.db.exists(
					"Otto Permission Request",
					{"session": self.session, "tool_use_id": ptu.id},
				)
			):
				continue

			req = OttoPermissionRequest.new(session=self.session, tool_use_id=ptu.id)
			if self.tool_permissions == "Allow All" or (
				config["is_readonly"] and self.tool_permissions == "Allow Readonly"
			):
				req.grant(is_autoset=True)
			else:
				requests.append(req)
		return requests

	def execute_tools(self, fn_map: dict[str, Callable] | None = None):
		from otto.otto.doctype.otto_tool.otto_tool import execute_tool

		fn_map = fn_map or {}
		pending_tools = self.get_permitted_pending_tools()
		yield pending_tools

		# Validate pending tools so as to avoid errors in the execution loop.
		for ptu in pending_tools:
			config = self._get_tool_config(ptu.name)
			if not config["is_external"] or fn_map.get(config["slug"]):
				continue
			raise ValueError(f"Function not found for external tool {config['slug']}")

		updates: list[ToolUseUpdate] = []
		try:
			for ptu in pending_tools:
				config = self._get_tool_config(ptu.name)
				fn = fn_map.get(config["slug"])
				update = execute_tool(
					tool=config["tool"],
					args=ptu.args,
					tool_use_id=ptu.id,
					env_str=None,
					permission_granted=True,
					task=None,
					session=self.session,
					chat=self.name,
					doc=None,
					fn=fn,
				)
				updates.append(update)
				yield update
		# Ensure all executed tools are updated; prevent double executions
		finally:
			self.update_tool_use(updates)
		return

	def get_permitted_pending_tools(self) -> list[PendingToolUse]:
		permitted = []
		req_map = self._get_requests_map()
		for ptu in self.get_pending_tools():
			# req_status is None if no request was raised for this tool.
			#
			# This can happen if the tool:
			# 1. Does not require permission
			# 2. The prerequisite `get_pending_requests` has not been called yet
			#
			# In the case of 1. execute_tools should be called again after the
			# request has been acknowledged.
			if (req_status := req_map.get(ptu.id)) and req_status != "Granted":
				continue

			permitted.append(ptu)
		return permitted

	def get_pending_tools(self) -> list[PendingToolUse]:
		if self._pending_tools is None:
			self._pending_tools = self.session_.get_pending_tool_use()
		return self._pending_tools

	def update_tool_use(self, update: ToolUseUpdate | list[ToolUseUpdate]) -> None:
		self._pending_tools = None
		self.session_.update_tool_use(update)

	def _get_requests_map(self) -> dict[str, RequestStatus]:
		requests = frappe.get_all(
			"Otto Permission Request",
			filters={"session": self.session},
			fields=["tool_use_id", "status"],
		)
		return {req.tool_use_id: req.status for req in requests}

	def _copy_tools(self, assistant: OttoAssistant):
		for tool in assistant.tools:
			self.append(
				"tools",
				{
					"tool": tool.tool,
					"slug": tool.slug,
					"is_enabled": tool.is_enabled,
					"requires_permission": tool.requires_permission,
				},
			)

	def _update_session_tools(self):
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		if not self._should_update_session_tools():
			return

		tool_schemas: list[lib.types.ToolSchema] = []
		for tool in self.tools:
			if not tool.is_enabled:
				continue

			schema = otto.get(
				OttoTool,
				tool.tool,
			).get_function_schema(tool.slug)
			tool_schemas.append(schema)
		self.session_.set_tools(tool_schemas)

	def _should_update_session_tools(self) -> bool:
		# Assumes that a tool's schema doesn't change mid session
		# only the list of tools used changes.
		tools = [tool for tool in self.tools if tool.is_enabled]
		if len(tools) != len(self.session_.tools):
			return True

		tool_map = {tool.slug: tool for tool in tools}
		for tool in self.session_.tools:
			if tool["name"] in tool_map:
				continue
			return True

		session_tool_map = {tool["name"]: tool for tool in self.session_.tools}
		for tool in tools:
			if tool.slug in session_tool_map:
				continue
			return True

		return False

	def update_settings(
		self,
		llm: str | None = None,
		reasoning_effort: ReasoningEffort | Literal["Default"] | None = None,
		tool_permissions: Literal[
			"Default",
			"Allow All",
			"Allow Readonly",
			"Ask For All",
			"Ask For Non Readonly",
		]
		| None = None,
		user_directives: str | None = None,
	):
		self.llm = llm
		self.reasoning_effort = "Default" if reasoning_effort is None else reasoning_effort
		self.user_directives = user_directives
		self.tool_permissions = tool_permissions or "Default"

		# Set here to prevent instruction update on every turn
		if not user_directives:
			instruction = self.assistant_.get_instruction()
			self.session_.set_instruction(instruction)

		self.save()

	def _ensure_settings_in_sync(self):
		# Ensure sync with chat settings
		if self.llm is not None and self.llm != self.session_.model:
			self.session_.set_model(self.llm)
		if self.reasoning_effort != "Default" and self.reasoning_effort != self.session_.reasoning_effort:
			self.session_.set_reasoning_effort(self.reasoning_effort)
		if self.user_directives is not None and self.user_directives not in self.session_.instruction:
			instruction = self.assistant_.get_instruction({"user_directives": self.user_directives})
			self.session_.set_instruction(instruction)

		# Reset clauses, ensure sync with assistant definition
		if (
			self.reasoning_effort == "Default" or not self.reasoning_effort
		) and self.session_.reasoning_effort != self.assistant_.reasoning_effort:
			self.session_.set_reasoning_effort(self.assistant_.reasoning_effort)
		if not self.llm and self.session_.model != self.assistant_.llm:
			self.session_.set_model(self.assistant_.llm)

		# Will cause instruction update on every turn
		# if (
		# 	not self.user_directives
		# 	and (instruction := self.assistant_.get_instruction()) != self.session_.instruction
		# ):
		# 	self.session_.set_instruction(instruction)


def generate_session_title(session: lib.Session) -> str | None:
	from otto.prompts.title import generate_chat_title

	model = lib.get_model(preference="gpt-5-nano", size="Very Small") or lib.get_model(size="Small")
	if not model:
		return None

	items = session.get_items()[:5]
	query = ""
	for item in items:
		if item["meta"]["role"] != "user":
			continue

		for content in item["content"]:
			if content["type"] != "text":
				continue

			query += f"User: {content['text']}\n"
	if not query:
		return None

	res = lib.quick_query(query, model=model, instruction=generate_chat_title, stream=False)
	if not res or res[0]["type"] != "text":
		return None

	return res[0]["text"].strip()
