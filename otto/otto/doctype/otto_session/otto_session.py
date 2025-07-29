# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

# import frappe
import json
import time
from typing import TYPE_CHECKING, Any, Literal, cast

import frappe
from frappe.model.document import Document

import otto
from otto import llm
from otto.llm.types import Session, ToolUseUpdate
from otto.llm.utils import get_last_id, get_session_list
from otto.otto.doctype.otto_task.tools import is_meta_tool

if TYPE_CHECKING:
	from otto.llm.types import Session, SessionItem

logger = otto.logger("otto_session")


class OttoSession(Document):
	"""Represents a single session with an LLM.

	An Otto Session can be a "Task" or a "Chat". It manages:
	- interaction history (i.e. the session)
	- tool availability (i.e. the tools)
	- tool execution

	This DocType acts as a persistent wrapper around the in-memory session
	representation used by the `otto.llm` module. The invoker of an OttoSession
	is responsible for managing the loop, invoking the tool calls.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from otto.otto.doctype.otto_session_item_ct.otto_session_item_ct import OttoSessionItemCT
		from otto.otto.doctype.otto_session_tool_ct.otto_session_tool_ct import OttoSessionToolCT

		first: DF.Data | None
		instruction: DF.Code | None
		is_active: DF.Check
		items: DF.Table[OttoSessionItemCT]
		llm: DF.Link | None
		reason: DF.SmallText | None
		reasoning_effort: DF.Literal["None", "Low", "Medium", "High"]
		tools: DF.Table[OttoSessionToolCT]
		type: DF.Literal["Task", "Chat"]
		uid: DF.Data | None
	# end: auto-generated types

	_osi_map: dict[str, OttoSessionItemCT] | None = None
	_last_item: SessionItem | None = None
	_session: Session | None = None

	@staticmethod
	def new(
		*,
		llm: str,
		instruction: str,
		reasoning_effort: str | None,
		session_type: Literal["Task", "Chat"],
	):
		doc = cast(OttoSession, frappe.get_doc({"doctype": "Otto Session"}))

		doc.llm = llm
		doc.instruction = instruction
		doc.type = session_type
		if reasoning_effort and reasoning_effort in ["None", "Low", "Medium", "High"]:
			doc.reasoning_effort = reasoning_effort  # type: ignore
		else:
			doc.reasoning_effort = "None"

		doc.save(ignore_permissions=True, ignore_version=True)
		return doc

	def interact(self, query: str | list[str] | None = None) -> tuple[SessionItem, None] | tuple[None, str]:
		"""Performs one turn of interaction with the LLM.

		This method sends the user's query, along with the current session context (history and tools),
		to the LLM. It then updates the session with the LLM's response.

		The caller is responsible for creating an interaction loop. This method only represents a
		single API call. After this, `run_tools` should be called if the LLM response includes
		tool use requests.

		Args:
		    query: The user's input for this turn. Can be a string, a list of strings, or None
		        to let the LLM continue its turn.

		Returns:
		    A tuple containing the latest session item and an error reason.
		    - `(SessionItem, None)` on success.
		    - `(None, str)` on failure, where the string is the error reason.
		"""
		from otto.otto.doctype.otto_llm.otto_llm import get_reasoning_effort

		self._set_status(is_active=True)

		try:
			interaction, reason = llm.interact(
				query,  # type: ignore needed cause not strong enough type system
				session=self._get_session(),
				tools=self._get_tools(),
				model=self.llm,
				system=self.instruction,
				reasoning_effort=get_reasoning_effort(self.reasoning_effort),
			)

			logger.info(
				{
					"message": "interact success",
					"session": self.name,
					"session_size": interaction and len(interaction["update"]),
					"item": interaction and interaction["item"],
				}
			)

		except Exception as e:
			otto.log_error(title="interact error", doc=self)
			reason = f"Interaction errored out: {e}"
			self._set_status(is_active=False, reason=reason)
			return None, reason

		if interaction is None:
			reason = reason or "No interaction returned"
			self._set_status(is_active=False, reason=reason)
			return None, reason

		self._set_status(is_active=False, session=interaction["update"])

		self._last_item = interaction["item"]
		return self._last_item, None

	def run_tools(self):
		"""Executes tool use requests from the last LLM response.

		This method inspects the last `SessionItem`. If it contains `tool_use` content,
		it executes the requested tools and appends the results to the session. It also
		handles special meta tools, like `end_task`.
		"""

		item = self.get_last_item()
		if item is None:
			return

		session = self._get_session()
		if session is None:
			return

		env_map = {t.name: t.env for t in self.tools}
		tool_map = self._get_tool_map()

		# Move meta tools to the end of the list
		content = sorted(item["content"], key=lambda x: is_meta_tool(x))

		for content in item["content"]:
			if content["type"] != "tool_use":
				continue

			# Used if meta tool
			update = ToolUseUpdate(
				start_time=time.time(),
				end_time=time.time(),
				is_error=False,
				result="",
				stdout=None,
				stderr=None,
			)

			if not is_meta_tool(content):
				tool_name = tool_map[content["name"]]
				env_str = env_map.get(tool_name, None)
				update = self._execute_tool(tool_name, content["args"], env_str)

			llm.update_with_tool_result(session=session, id=content["id"], update=update)
			self._set_session(session)

	def get_last_item(self) -> SessionItem | None:
		if self._last_item:
			return self._last_item

		session = self._get_session()
		if session is None:
			return None

		id = get_last_id(session)
		return session["items"].get(id)

	def _set_status(
		self,
		is_active: bool,
		*,
		reason: str | None = None,
		session: Session | None = None,
	):
		self.is_active = is_active
		self.reason = reason
		if session is not None:
			self._set_session(session)

		self.save(ignore_permissions=True, ignore_version=True)
		frappe.db.commit()

	def _get_session(self) -> None | Session:
		if not self.uid or not self.first:
			# no session yet, will be created on first interaction
			return None

		if self._session is not None:
			return self._session

		session = Session(
			id=self.uid,
			first=self.first,
			items={},
		)

		self._set_osi_map()
		assert self._osi_map is not None, "type check"
		for item in self.items:
			self._osi_map[item.uid] = item
			session["items"][item.uid] = item.to_session_item()
		self._session = session

		return session

	def _set_session(self, session: Session) -> None:
		from otto.otto.doctype.otto_session_item_ct.otto_session_item_ct import OttoSessionItemCT

		self.uid = session["id"]
		self.first = session["first"]
		self._session = session

		# reset sequence incase active list has changed
		self.items.clear()
		added = set()
		self._set_osi_map()
		assert self._osi_map is not None, "type check"

		# Active sequence items first
		for item in get_session_list(session):
			osi = self._osi_map.get(item["id"])
			if not osi:
				osi = OttoSessionItemCT.from_session_item(item)
			else:
				osi.sync_with_session_item(item)
			osi.is_selected = True
			added.add(item["id"])
			self.append("items", osi)

		# Rest of the non-active items
		for uid, item in session["items"].items():
			if uid in added:
				continue

			osi = self._osi_map.get(uid)
			if not osi:
				osi = OttoSessionItemCT.from_session_item(item)
			else:
				osi.sync_with_session_item(item)

			osi.is_selected = False
			self.append("items", osi)

		self.save(ignore_permissions=True, ignore_version=True)
		frappe.db.commit()

	def get_count_of_llm_calls(self, selected: bool = False):
		"""
		If selected is True, returns the number of LLM calls in the selected items.
		If selected is False returns total count including selected and non-selected items.
		"""
		count = 0
		for item in self.items:
			if (selected and not item.is_selected) or item.role != "agent":
				continue

			count += 1
		return count

	def _execute_tool(self, tool_name: str, args: dict, env_str: str | None) -> ToolUseUpdate:
		"""Executes tool and returns tuple of (result, is_error)"""
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		tool_doc = otto.get(OttoTool, tool_name)
		update = ToolUseUpdate(
			start_time=time.time(),
			end_time=time.time(),
			is_error=False,
			result="",
			stdout=None,
			stderr=None,
		)

		try:
			env = json.loads(env_str) if env_str else None
			result = tool_doc.execute(
				args,
				task=self._get_task_name(),
				session=self.name,
				env=env,
			)
			update["is_error"] = False
			update["result"] = result["result"]
			update["stdout"] = result["stdout"]
			update["stderr"] = result["stderr"]
			update["end_time"] = time.time()
		except Exception as e:
			otto.log_error(
				"Tool Use Error",
				doc=self,
				tool=tool_name,
			)
			update["is_error"] = True
			update["result"] = str(e)
			update["end_time"] = time.time()
		return update

	def _get_task_name(self) -> str | None:
		if self.type != "Task":
			return None

		exec_tasks = frappe.get_all("Otto Execution", filters={"session": self.name}, pluck="task", limit=1)
		if not exec_tasks or not isinstance(exec_tasks[0], str):
			return None

		return exec_tasks[0]

	@frappe.whitelist()
	def get_stats(self):
		if not (session := self._get_session()):
			return None

		return llm.get_stats(session)

	def _set_osi_map(self) -> None:
		"""Sets _osi_map if not already set, should be used only in get_session and set_session"""
		if hasattr(self, "_osi_map") and self._osi_map is not None:
			return
		self._osi_map = {}

	def _get_tools(self):
		from otto.otto.doctype.otto_task.tools import meta_tools
		from otto.otto.doctype.otto_tool.otto_tool import OttoTool

		tools = []
		for tool in self.tools:
			tool_doc = otto.get(OttoTool, tool.tool)
			if not tool_doc.is_valid:
				continue

			tools.append(tool_doc.get_function_schema(tool.slug))

		tools.extend(meta_tools)
		return tools

	def _get_tool_map(self) -> dict[str, str]:
		"""returns dict[slug, name]"""
		names = [t.tool for t in self.tools if not t.slug and t.is_enabled]
		_tool_map = {
			t.name: t.slug
			for t in frappe.get_all("Otto Tool", filters={"name": ("in", names)}, fields=["slug", "name"])
		}

		tool_map = {}
		for t in self.tools:
			if not t.is_enabled:
				continue

			slug = t.slug or _tool_map[t.tool]
			tool_map[slug] = t.tool
		return tool_map
