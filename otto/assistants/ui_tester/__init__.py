from otto.assistants.utils import get_tool

uid = "otto-ui-tester"
name = "UI Tester"
dev_mode_only = True

instruction = """
You are {{name}} a helpful assistant. You are currently speaking to {{user}} and the date is {{date}}.
# Communication Directives
Keep all your responses short and to the point.
# Tool Use Directives
Use the `log` tool when the user asks to log something
Use the `secure_log` tool when the user asks to log something securely.
"""

preferred_model = "openai/gpt-5-nano"
preferred_config = {"size": "Very Small"}
reasoning_effort = "None"


def get_context():
	import frappe
	import frappe.utils

	return {"user": frappe.session.user, "date": frappe.utils.now()}


def log(content: str) -> str:
	"""Log a message (non-secure).

	Args:
		content: The message to log.
	"""
	return "Success"


def secure_log(content: str) -> str:
	"""Log a message securely.

	Args:
		content: The message to log securely.
	"""
	return "Success"


tools = [
	get_tool(
		log,
		uid="ui-tester-log-tool",
		dev_mode_only=True,
		is_open_world=False,
	),
	get_tool(
		secure_log,
		uid="ui-tester-secure-log-tool",
		requires_permission=True,
		dev_mode_only=True,
		is_open_world=False,
	),
]
