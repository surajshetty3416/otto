# Copyright (c) 2025, Alan Tom and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, cast

import frappe
from frappe.model.document import Document

from otto.llm.types import EndReason, Meta, SessionItem, SessionRole

if TYPE_CHECKING:
	from frappe.types import DF


class OttoSessionItemCT(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		content: DF.JSON
		cost: DF.Float
		end_reason: DF.Data | None
		end_time: DF.Datetime | None
		input_tokens: DF.Int
		inter_chunk_latency: DF.Float
		is_selected: DF.Check
		model: DF.Data | None
		next: DF.SmallText | None
		output_tokens: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		role: DF.Data
		selected: DF.Int
		start_time: DF.Datetime | None
		time_to_first_chunk: DF.Float
		timestamp: DF.Datetime
		uid: DF.Data
	# end: auto-generated types

	@staticmethod
	def from_session_item(item: SessionItem) -> OttoSessionItemCT:
		osi = cast("OttoSessionItemCT", frappe.new_doc("Otto Session Item CT"))
		osi.sync_with_session_item(item)
		return osi

	def sync_with_session_item(self, item: SessionItem):
		# ID
		self.uid = item["id"]
		self.next = json.dumps(item["next"])
		self.selected = item["selected_next"]

		# Meta
		self.role = item["meta"]["role"]
		self.model = item["meta"]["model"]
		self.input_tokens = item["meta"]["input_tokens"]
		self.output_tokens = item["meta"]["output_tokens"]
		self.cost = item["meta"]["cost"]

		self.timestamp = datetime.fromtimestamp(item["meta"]["timestamp"])
		self.start_time = datetime.fromtimestamp(item["meta"]["start_time"])
		self.end_time = datetime.fromtimestamp(item["meta"]["end_time"])

		self.time_to_first_chunk = item["meta"]["time_to_first_chunk"] or 0
		self.inter_chunk_latency = item["meta"]["inter_chunk_latency"] or 0

		self.end_reason = item["meta"]["end_reason"]

		# Content
		self.content = json.dumps(item["content"], indent=2)

	def to_session_item(self) -> SessionItem:
		return SessionItem(
			id=self.uid,
			next=json.loads(self.next or "[]"),
			selected_next=self.selected,
			meta=Meta(
				role=self._get_role(),
				model=self.model,
				input_tokens=self.input_tokens,
				output_tokens=self.output_tokens,
				cost=self.cost,
				timestamp=get_timestamp(self.timestamp),
				start_time=get_timestamp(self.start_time),
				end_time=get_timestamp(self.end_time),
				end_reason=self._get_end_reason(),
				time_to_first_chunk=self.time_to_first_chunk or 0,
				inter_chunk_latency=self.inter_chunk_latency or 0,
			),
			content=json.loads(self.content),
		)

	def _get_role(self) -> SessionRole:
		if self.role == "user" or self.role == "agent":
			return self.role

		# Bad default (but so is "user")
		return "user"

	def _get_end_reason(self) -> EndReason | None:
		if self.end_reason == "turn_end" or self.end_reason == "tool_use":
			return self.end_reason

		return None


def get_timestamp(dt: DF.Datetime | None) -> float:
	if not dt:
		return 0

	if isinstance(dt, str):
		dt = datetime.fromisoformat(dt)

	return dt.timestamp()
