import frappe


@frappe.whitelist()
def chat(message: str, session: str | None = None):
	"""
	Use to resume or start a new chat session, if session is provided then
	resume, else new.
	"""
	pass


def load(session: str):
	"""
	Load the messages of a session to display on the UI.
	"""
	pass


def list():
	"""
	    List sessions for the sidebar, on clicking load will be called and the user
	can then resume a chat

	List should pull up the sessions along with assistant that was used to create
	the session
	"""
	pass
