import frappe


@frappe.whitelist()
def test():
	return "success"


@frappe.whitelist()
# def chat(query: str, session: str | None = None):
def chat(query: str):
	from otto.api.dummy import chat

	"""
	Use to resume or start a new chat session, if session is provided then
	resume, else new.
	"""
	frappe.enqueue(
		# TODO: wrap chat in a try catch; on error always communicate
		chat,
		timeout=300,
		at_front=True,
		query=query,
	)
	return {"status": "Success"}


@frappe.whitelist()
def load(session: str):
	"""
	Load the messages of a session to display on the UI.
	"""
	pass


@frappe.whitelist()
def list_chats():
	"""
		List sessions for the sidebar, on clicking load will be called and the user
	can then resume a chat

	List should pull up the sessions along with assistant that was used to create
	the session
	"""
	pass


@frappe.whitelist()
def list_assistants():
	"""
	List assistants that the user can use to chat with.

	Once an assistant is selected the user cannot change it for a
	chat session. The user can configure the underlying session by
	selecting the LLM and available tools but not the assistant.
	"""
	pass
