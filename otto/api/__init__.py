import frappe


@frappe.whitelist(allow_guest=True, methods=["GET"])
def log_feedback():
	"""Submit feedback to the server."""
	from otto.otto.doctype.otto_feedback.otto_feedback import OttoFeedback, get_value

	res = OttoFeedback.log(
		name=frappe.request.args.get("name"),
		value=get_value(frappe.request.args.get("value")),
		session=frappe.request.args.get("session"),
		comment=frappe.request.args.get("comment"),
	)

	return dict(
		message=res["message"],
		reason=res["reason"],
		name=res["feedback"].name if res["feedback"] else None,
	)
