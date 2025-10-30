from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast

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

	from otto.lib.types import PendingToolUse, Query, ToolUseUpdate
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


class OttoChat(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_chat_tool_ct.otto_chat_tool_ct import OttoChatToolCT

		assistant: DF.Link
		session: DF.Link
		title: DF.Data | None
		tools: DF.Table[OttoChatToolCT]
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
	def new(assistant: str) -> OttoChat:
		from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		doc = cast("OttoChat", frappe.new_doc("Otto Chat"))
		assistant_doc = otto.get(OttoAssistant, assistant)
		doc.assistant = assistant

		reasoning_effort = assistant_doc.reasoning_effort
		if reasoning_effort == "None":
			reasoning_effort = None

		tool_schemas: list[lib.types.ToolSchema] = []
		for tool_ref in assistant_doc.tools:
			if not tool_ref.is_enabled:
				continue

			tool_doc = otto.get(OttoTool, tool_ref.tool)
			schema = tool_doc.get_function_schema(slug=tool_ref.slug)
			tool_schemas.append(schema)

		session = lib.new(
			model=assistant_doc.llm or DEFAULT_MODEL,
			instruction=assistant_doc.get_instruction(),
			reasoning_effort=reasoning_effort,
			tools=tool_schemas,
		)
		doc.session_ = session
		doc._copy_tools(assistant_doc)
		doc.title = "New Chat with " + (assistant_doc.title or "Assistant")

		doc.save()
		return doc

	def autoset_title(self):
		# TODO: use a small model to generate a title from the first 4 exchanges
		...

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

	def get_pending_requests(self) -> list[OttoPermissionRequest]:
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
		old_requests = [otto.get(OttoPermissionRequest, req) for req in old_requests_names]
		return new_requests + old_requests

	def _raise_permissions_requests(self) -> list[OttoPermissionRequest]:
		requests: list[OttoPermissionRequest] = []
		pending_tool_use = self.get_pending_tools()
		for ptu in pending_tool_use:
			config = self.tool_config_map.get(ptu.name)
			if not config or not config["requires_permission"]:
				continue

			if bool(
				frappe.db.exists(
					"Otto Permission Request",
					{"session": self.session, "tool_use_id": ptu.id},
				)
			):
				continue

			req = OttoPermissionRequest.new(session=self.session, tool_use_id=ptu.id)
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
