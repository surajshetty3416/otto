from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, cast

# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

import otto
import otto.lib as lib
from otto.llm.utils import DEFAULT_MODEL
from otto.otto.doctype.otto_assistant.otto_assistant import OttoAssistant
from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest

if TYPE_CHECKING:
	from collections.abc import Callable

	from otto.lib.types import PendingToolUse, Query, ToolUseUpdate


class ToolConfig(NamedTuple):
	slug: str
	tool: str  # Otto Tool name
	is_external: bool
	requires_permission: bool


class OttoChat(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		assistant: DF.Link
		session: DF.Link
		title: DF.Data | None
	# end: auto-generated types

	_session: lib.Session | None = None
	_assistant: OttoAssistant | None = None
	_pending_tool_use: list[PendingToolUse] | None = None
	_tool_configs: dict[str, ToolConfig] | None = None

	@property
	def tool_configs(self) -> dict[str, ToolConfig]:
		"""Returns: dict[slug, otto_tool_name]"""
		if self._tool_configs is not None:
			return self._tool_configs

		map: dict[str, ToolConfig] = {}
		tool_names = [tool.tool for tool in self.assistant_.tools]

		tools = {
			t.name: t
			for t in frappe.get_all(
				"Otto Tool",
				filters={"name": ["in", tool_names]},
				fields=["name", "slug", "is_external", "requires_permission"],
			)
		}

		for tool in self.assistant_.tools:
			if not tool.slug:
				continue

			td = tools[tool.tool]
			map[tool.slug] = ToolConfig(
				slug=tool.slug,
				tool=tool.tool,
				is_external=bool(td.is_external),
				requires_permission=bool(tools[tool.tool].requires_permission or td.requires_permission),
			)

		self._tool_configs = map
		return map

	@property
	def assistant_(self) -> OttoAssistant:
		if not self._assistant:
			self._assistant = otto.get(OttoAssistant, self.assistant)
		return self._assistant

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

		doc.save()
		return doc

	def chat(self, query: Query | None = None):
		"""query can be None when resuming after a tool use request"""
		if self.has_pending_requests():
			return None, "Resolve all pending requests before resuming chat"

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
			config = self.tool_configs.get(ptu.name)
			if not config or not config.requires_permission:
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
			config = self.tool_configs.get(ptu.name)
			if not config:
				continue

			fn = fn_map.get(config.slug)
			if config.is_external and not fn:
				# External tool call managed by caller
				continue

			req_status = req_map.get(ptu.id)
			if not (req_status is None or req_status == "Granted"):
				continue

			update = execute_tool(
				tool=config.tool,
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
			config = self.tool_configs.get(ptu.name)
			if not config or not config.is_external:
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
