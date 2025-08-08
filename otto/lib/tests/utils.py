import contextlib

import frappe

from otto.lib.session import Session


def print_stats(sessions: list[Session]):
	from otto.llm.test_llm.utils import print_stats as print_stats_inner

	print_stats_inner([session.get_stats() for session in sessions])


def delete_sessions(sessions: list[Session]):
	for session in sessions:
		with contextlib.suppress(Exception):
			frappe.delete_doc("Otto Session", session.id, force=True)

	frappe.db.commit()
