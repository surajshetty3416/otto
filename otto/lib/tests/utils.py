import contextlib

import frappe

from otto.lib.session import Session


def print_stats(sessions: list[Session]):
	"""Use to print stats for sessions after tests"""
	from otto.llm.test_llm.utils import print_stats as print_stats_inner

	print_stats_inner([session.get_stats() for session in sessions])


def delete_sessions(sessions: list[Session]):
	"""Use to clean up sessions after tests"""
	for session in sessions:
		with contextlib.suppress(Exception):
			frappe.delete_doc("Otto Session", session.id, force=True)

	frappe.db.commit()


def print_session(session: Session):
	"""Use to debug a session"""
	from otto.lib.types import Content

	def _print_content(content: list[Content]):
		if len(content) == 1 and content[0]["type"] == "text":
			print(" ", end="")
			print(content[0]["text"])
			return

		print()
		for c in content:
			print("     - ", end="")
			if c["type"] == "text":
				print(f"text: {c['text']}")
			elif c["type"] == "image":
				val = c["url"]
				if not val and c["data"]:
					val = c["data"][:32]
				if not val:
					val = "<empty>"

				print(f"image: {val}")
			elif c["type"] == "file":
				print(f"file: {c['name']}")
			elif c["type"] == "thinking":
				print(f"thinking: {c['text']}")
			elif c["type"] == "tool_use":
				print(f"tool_use: {c['name']} {c['args']}")

	idx = 1
	for item in session.get_items():
		print(f"[{idx:02d}]", end=" ")
		if item["meta"]["role"] == "user":
			print("user:", end="")
		else:
			print("llm: ", end="")
		_print_content(item["content"])
		idx += 1
