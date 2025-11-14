from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

import frappe

import otto
from otto.api.types import RealtimeError

if TYPE_CHECKING:
	from otto.api.types import RealtimeChatMessage

logger = otto.logger("otto.api.utils", "INFO")


def inform_on_error(fn):
	"""
	Decorator to inform if an error has occurred in a background task.  Use this
	on the root function of a background task (i.e. the function that) is
	enqueued.
	"""

	from functools import wraps

	@wraps(fn)
	def wrapper(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		except Exception as e:
			publish_activity(
				RealtimeError(
					id=frappe.generate_hash(length=10),
					traceback=traceback.format_exc() if e.__traceback__ else None,
					data=str(e),
					chat_id=None,
					type="error",
				)
			)
			raise e

	return wrapper


def publish_activity(message: RealtimeChatMessage, after_commit: bool = False) -> None:
	frappe.publish_realtime(
		"otto.api.chat",
		user=frappe.session.user,
		message=dict(message),
		after_commit=after_commit,
	)
	logger.debug(
		{
			"message": "published message",
			"user": frappe.session.user,
			"data": dict(message),
		}
	)
