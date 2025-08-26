import frappe


@frappe.whitelist(allow_guest=True)
def ping():
	return "pong"


@frappe.whitelist()
def get_user() -> dict[str, str]:
	assert isinstance(frappe.session.user, str), "User is not logged in"
	return {"user": frappe.session.user}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def log_feedback():
	"""
	Used to log feedback for Otto's performance on a task execution or a
	standalone session.


	### Without UI

	This url can be called directly to log feedback as an Otto Feedback entry.

	Use query params when providing feedback:
	- name: existing Otto Feedback name, if provided then existing feedback will
		be updated.
	- session: session name, if provided then feedback will be logged for the
		session (execution links to the session)
	- value: 1 or -1 for :thumbs-up: or :thumbs-down: to answer "Was Otto helpful?"
	- comment: additional user provided comment

	Base URL:
		`/api/method/otto.api.log_feedback`

	Examples:

	- Log :thumbs-up: and a comment for session:
		/api/method/otto.api.log_feedback?session=$SESSION_NAME&value=1&comment=This%20was%20helpful
	- Log :thumbs-down: for session:
		/api/method/otto.api.log_feedback?session=$SESSION_NAME&value=-1
	- Update feedback for existing feedback:
		/api/method/otto.api.log_feedback?name=$FEEDBACK_NAME&session=$SESSION_NAME&value=1

	If session is not provided then feedback will still be logged.


	### With UI

	To show UI for feedback, redirect the user to `/otto_feedback` with
	`session` as a query parameter.

	If additional query params for `comment` or `value` [1, -1] are provided
	then feedback will be optimistically logged before the UI is shown. And on
	submit the feedback will then be updated.

	Base URL:
		`/otto_feedback`

	UI Redirect Examples:
	- Collect feedback for session:
		/otto_feedback?session=$SESSION_NAME
	- Optimistically log :thumbs-down:
		/otto_feedback?session=$SESSION_NAME&value=-1
	- Optimistically log :thumbs-up: and comment:
		/otto_feedback?session=$SESSION_NAME&value=1&comment=This%20was%20helpful
	- Update feedback on submit for existing feedback:
		/otto_feedback?name=$FEEDBACK_NAME&session=$SESSION_NAME&value=1

	When Submit is clicked in the UI this function is called to create or update
	an Otto Feedback entry.
	"""

	from otto.otto.doctype.otto_feedback.otto_feedback import OttoFeedback, get_value

	res = OttoFeedback.log(
		name=frappe.request.args.get("name"),
		value=get_value(frappe.request.args.get("value")),
		session=frappe.request.args.get("session"),
		comment=frappe.request.args.get("comment"),
	)
	frappe.db.commit()

	return dict(
		message=res["message"],
		reason=res["reason"],
		name=res["feedback"].name if res["feedback"] else None,
	)
