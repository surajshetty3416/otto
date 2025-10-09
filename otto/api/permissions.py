from typing import Literal

import frappe

import otto


@frappe.whitelist(methods=["POST"])
def add_viewed(name: str):
	from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest

	otto.get(OttoPermissionRequest, name).add_viewed()


@frappe.whitelist(methods=["POST"])
def acknowledge(
	name: str,
	type: Literal["grant", "deny"],
	override_args: dict | None = None,
):
	"""
	Acknowledge and update the status of an Otto Permission Request.

	This API endpoint processes permission requests by either granting or denying them.
	It updates the status of the specified permission request and optionally allows
	overriding the original request arguments.

	Args:
		name: The name of the Otto Permission Request doc to acknowledge.
		type: The action to take - either "grant" to approve
			or "deny" to reject the permission request.
		override_args: A dictionary of arguments to override
			the original permission request parameters. Defaults to None.

	Returns:
		None: Returns early if name is empty or type is invalid.

	Example:
		acknowledge(name=perm_req_name, type="grant", override_args={"limit": 100})
	"""
	from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest

	if not name or type not in ["grant", "deny"]:
		return

	status = "Granted" if type == "grant" else "Denied"

	opr = otto.get(OttoPermissionRequest, name)
	opr.add_viewed()
	opr.acknowledge(status, override_args)


@frappe.whitelist(methods=["POST"])
def get_pending_requests(
	task: str | None = None,
	execution: str | None = None,
	target: str | None = None,
	tool_slug: str | None = None,
	tool_name: str | None = None,
	target_doctype: str | None = None,
	session: str | None = None,
	tool_use_id: str | None = None,
):
	"""
	Retrieve pending Otto Permission Requests based on various filter criteria.

	This API endpoint queries the database for permission requests with a "Pending" status
	and applies various filters to narrow down the results. It can filter by session,
	execution, task, target, tool identifiers, and more.

	Args:
		task: Filter by Otto Task name/ID. Defaults to None.
		execution: Filter by Otto Execution name/ID. Defaults to None.
		target: Filter by execution target. Defaults to None.
		tool_slug: Filter by tool slug identifier. Defaults to None.
		tool_name: Filter by tool name. Defaults to None.
		target_doctype: Filter by target doctype. Defaults to None.
		session: Filter by Otto Session name/ID. If provided,
			directly queries permission requests for this session. Defaults to None.
		tool_use_id: Filter by specific tool use identifier.
			Defaults to None.

	Returns:
		list[dict]: A list of permission request dictionaries. Returns an empty list
			if no matching requests are found.

	Note:
		When a session is provided, the function takes a direct query path. Otherwise,
		it first finds matching Otto Executions and then queries permission requests
		associated with those executions' sessions.

	Example:
		get_pending_requests(session=session_name, tool_slug="read_file")
	"""
	opr_filters: dict = {"status": "Pending"}

	if tool_use_id:
		opr_filters["tool_use_id"] = tool_use_id

	if session:
		opr_filters["session"] = session
		requests = frappe.get_all(
			"Otto Permission Request",
			filters=opr_filters,
			pluck="name",
		)
		return _get_requests(requests, tool_slug, tool_name)

	execution_filters = {}
	if execution:
		execution_filters["name"] = execution

	if task:
		execution_filters["task"] = task

	if target:
		execution_filters["target"] = target

	if target_doctype:
		execution_filters["target_doctype"] = target_doctype

	sessions = frappe.get_all(
		"Otto Execution",
		filters=execution_filters,
		fields=["session"],
		pluck="session",
	)
	opr_filters["session"] = ("in", sessions)
	requests = frappe.get_all(
		"Otto Permission Request",
		filters=opr_filters,
		pluck="name",
	)
	return _get_requests(requests, tool_slug, tool_name)


def _get_requests(names: list[str], tool_slug: str | None, tool_name: str | None):
	from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest

	requests: list[dict] = []

	for name in names:
		opr = otto.get(OttoPermissionRequest, name)
		if tool_slug and opr.tool_slug != tool_slug:
			continue

		if tool_name and opr.tool_name != tool_name:
			continue

		request = opr.as_dict()
		request.pop("doctype", None)
		request.pop("docstatus", None)
		request.pop("idx", None)
		request.pop("tool_use_result", None)
		requests.append(request)

	return requests
