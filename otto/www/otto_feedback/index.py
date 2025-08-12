import frappe

# See otto.api.log_feedback for more details.


def get_context(context):
	from otto.otto.doctype.otto_feedback.otto_feedback import OttoFeedback, get_value

	name = frappe.request.args.get("name")
	value = get_value(frappe.request.args.get("value"))
	session = frappe.request.args.get("session")
	comment = frappe.request.args.get("comment")

	feedback = None

	# Optimistically log feedback if either of these are set, allows embedding
	# thumbs up/down buttons into the url itself.
	if comment or value:
		log = OttoFeedback.log(
			name=name,
			session=session,
			value=value,
			comment=comment,
		)
		feedback = log["feedback"]

	if feedback:
		context.name = feedback.name
		context.value = feedback.value
		context.comment = feedback.comment
		context.session = feedback.session
		frappe.db.commit()  # ensure that feedback is created before returning
	else:
		context.name = None  # Feedback will be created on Submit
		context.value = value or 0
		context.comment = comment
		context.session = session

	if session and (target := get_target(session)):
		context.task_title = target["task_title"]
		context.target_doctype = target["target_doctype"]
		context.target = target["target"]

	return context


def get_target(otto_session: str) -> dict | None:
	if targets := frappe.get_all(
		"Otto Execution",
		filters={"session": otto_session},
		fields=["target_doctype", "target", "task"],
		limit=1,
	):
		target = targets[0]
		target["task_title"] = frappe.get_cached_value("Otto Task", target["task"], "title")
		return target

	return None
