from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, cast, overload

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

import otto
import otto.lib as lib
from otto.llm.utils import DEFAULT_MODEL
from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest

if TYPE_CHECKING:
	from collections.abc import Callable

	from otto.lib.types import PendingToolUse, Query, ReasoningEffort, ToolUseUpdate
	from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant


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
		reasoning_effort: DF.Literal["None", "Low", "Medium", "High"] | None
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
		reasoning_effort: ReasoningEffort | None = None,
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
		doc.tool_permissions = tool_permissions or "Default"
		doc.user_directives = user_directives
		doc.reasoning_effort = reasoning_effort

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

		session = lib.new(
			model=llm or assistant_doc.llm or DEFAULT_MODEL,
			instruction=assistant_doc.get_instruction(context),
			reasoning_effort=reasoning_effort or assistant_doc.reasoning_effort,
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
		return self.session_.interact(query, stream=True), None

	def has_pending_requests(self) -> bool:
		self._raise_permissions_requests()
		rm = self._get_requests_map()
		return any(status == "Pending" for status in rm.values())

	def can_resume(self):
		"""
		A chat can be resumed only if all pending requests have been resolved,
		all pending tools have been executed and the reason an LLM stopped
		generation was for tool execution.
		"""

		if self.has_pending_requests():
			return False

		if self.get_pending_tools():
			return False

		last_item = self.session_.get_last_item()
		if not last_item:
			return False

		return last_item["meta"]["role"] == "agent" and last_item["meta"]["end_reason"] == "tool_use"

	@overload
	def get_pending_requests(self, name_only: Literal[False] = False) -> list[OttoPermissionRequest]: ...

	@overload
	def get_pending_requests(self, name_only: Literal[True]) -> list[str]: ...

	def get_pending_requests(self, name_only: bool = False) -> list[OttoPermissionRequest] | list[str]:
		new_requests = self._raise_permissions_requests()
		new_requests_names = [req.name for req in new_requests]
		old_requests_names = frappe.get_all(
			"Otto Permission Request",
			filters={
				"name": ["not in", new_requests_names],
				"session": self.session,
				"status": "Pending",
			},
			pluck="name",
		)

		if name_only:
			return [req.name for req in new_requests if req.name] + old_requests_names

		old_requests = [otto.get(OttoPermissionRequest, req) for req in old_requests_names]
		return new_requests + old_requests

	def _raise_permissions_requests(self) -> list[OttoPermissionRequest]:
		requests: list[OttoPermissionRequest] = []
		pending_tool_use = self.get_pending_tools()
		for ptu in pending_tool_use:
			config = self.tool_config_map.get(ptu.name)
			if not config:
				raise ValueError(f"Tool config not found for {ptu.name}")

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
		req_map = self._get_requests_map()
		updates: list[ToolUseUpdate] = []
		for ptu in self.get_pending_tools():
			config = self.tool_config_map.get(ptu.name)
			if not config:
				continue

			fn = fn_map.get(config["slug"])
			if config["is_external"] and not fn:
				# External tool call managed by caller
				continue

			req_status = req_map.get(ptu.id)
			if not (req_status is None or req_status == "Granted"):
				continue

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
		self.update_tool_use(updates)
		return

	def get_pending_tools(self, include_external: bool = True) -> list[PendingToolUse]:
		pending_tool_uses = self.session_.get_pending_tool_use()
		if include_external:
			return pending_tool_uses

		pending: list[PendingToolUse] = []
		for ptu in pending_tool_uses:
			config = self.tool_config_map.get(ptu.name)
			if not config or not config["is_external"]:
				continue

			pending.append(ptu)
		return pending

	def update_tool_use(self, update: ToolUseUpdate | list[ToolUseUpdate]) -> None:
		self.session_.update_tool_use(update)

	def _get_requests_map(self) -> dict[str, str]:
		requests = frappe.get_all(
			"Otto Permission Request",
			filters={"session": self.session},
			fields=["tool_use_id", "status", "denied_reason"],
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
		reasoning_effort: ReasoningEffort | None = None,
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
		from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant

		if llm:
			self.llm = llm
			self.session_.set_model(llm)

		if reasoning_effort:
			self.reasoning_effort = reasoning_effort
			self.session_.set_reasoning_effort(reasoning_effort)

		if user_directives:
			self.user_directives = user_directives
			context = {"user_directives": user_directives}
			instruction = otto.get(OttoAssistant, self.assistant).get_instruction(context)
			self.session_.set_instruction(instruction)

		if tool_permissions:
			self.tool_permissions = tool_permissions

		self.save()


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
