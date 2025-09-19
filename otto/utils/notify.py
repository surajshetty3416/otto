from typing import TypedDict

import frappe

import otto
from otto import utils

logger = otto.logger("otto.utils.notify", level="DEBUG")


class PermissionRequest(TypedDict):
	# Context
	task: str
	execution: str
	session: str
	permission: str

	# Target
	target: str | None
	target_doctype: str | None

	# Tool
	tool: str | None  # Otto Tool doc name
	tool_slug: str
	tool_use_id: str
	tool_args: dict


def notify(perms: list[PermissionRequest]):
	"""Sends notification to all assigned users for tool use request"""
	logger.debug({"message": "notifying", "perms": perms})

	users_map: dict[tuple[str, str], list[PermissionRequest]] = {}

	assigned_users = _get_assigned_users(perms)
	user_assignments: dict[str, dict[str, set[tuple[str, str]]]] = {}

	for perm in perms:
		target_assigned = assigned_users.get((perm["target_doctype"] or "", str(perm["target"] or "")), set())
		task_assigned = assigned_users.get(("Otto Task", perm["task"]), set())
		tool_assigned = assigned_users.get(("Otto Tool", perm["tool"] or ""), set())
		exec_assigned = assigned_users.get(("Otto Execution", perm["execution"]), set())
		session_assigned = assigned_users.get(("Otto Session", perm["session"]), set())
		assigned = target_assigned | task_assigned | tool_assigned | exec_assigned | session_assigned

		for user in assigned:
			assignments = []
			if user in target_assigned and perm["target_doctype"] and perm["target"]:
				assignments.append((perm["target_doctype"], perm["target"]))
			if user in task_assigned:
				assignments.append(("Otto Task", perm["task"]))
			if user in tool_assigned:
				assignments.append(("Otto Tool", perm["tool"] or ""))
			if user in exec_assigned:
				assignments.append(("Otto Execution", perm["execution"]))
			if user in session_assigned:
				assignments.append(("Otto Session", perm["session"]))

			user_assignments.setdefault(user, {}).setdefault(perm["permission"], set()).update(assignments)
			users_map.setdefault((user, perm["permission"]), []).append(perm)

	for (user, _), perms in users_map.items():
		_notify(
			user=user,
			perms=perms,
			assignments=user_assignments.get(user, {}).get(perms[0]["permission"], set()),
		)


def _get_assigned_users(
	perms: list[PermissionRequest],
):
	targets: list[tuple[str, str]] = list(
		set(
			(perm["target_doctype"], perm["target"])
			for perm in perms
			if perm["target"] and perm["target_doctype"]
		)
	)
	executions = list(set(perm["execution"] for perm in perms))
	sessions = list(set(perm["session"] for perm in perms))
	tasks = list(set(perm["task"] for perm in perms))
	tools = list(set(perm["tool"] for perm in perms if perm["tool"]))

	# Implementation from doc.get_assigned_users
	reference_types = ["Otto Task", "Otto Tool", "Otto Execution", "Otto Session"]
	reference_names = [*tasks, *tools, *executions, *sessions]

	for target_doctype, target in targets:
		reference_names.append(target)
		reference_types.append(target_doctype)

	assigned_users = frappe.get_all(
		"ToDo",
		fields=["allocated_to", "reference_type", "reference_name"],
		filters={
			"reference_type": ["in", list(set(reference_types))],
			"reference_name": ["in", list(set(reference_names))],
			"status": ("!=", "Cancelled"),
		},
	)
	logger.debug({"message": "getting assigned", "assigned_users": assigned_users})

	assignment_map: dict[tuple[str, str], set[str]] = {}
	for user in assigned_users:
		assignment_map.setdefault((user.reference_type, str(user.reference_name)), set()).add(
			user.allocated_to
		)

	return assignment_map


def _notify(
	user: str,
	perms: list[PermissionRequest],
	assignments: set[tuple[str, str]],
):
	"""Send notification to user for permission request"""
	from frappe.desk.doctype.notification_log.notification_log import NotificationLog

	assignments_str = ", ".join([f"{doctype} - {name}" for doctype, name in assignments])

	perm = PermissionRequest(**perms[0])
	for p in perms:
		for key, value in p.items():
			if key in perm and perm.get(key):
				continue
			perm[key] = value

	if _skip_notification(user, perm["permission"]):
		logger.debug(
			{
				"message": "notification skipped",
				"user": user,
				"perm_req": perm["permission"],
			}
		)
		return

	tool_title = perm["tool_slug"]
	if perm["tool"]:
		tool_title = (
			frappe.get_cached_value(
				"Otto Tool",
				perm["tool"],
				"title",
			)
			or perm["tool_slug"]
		)
	task_title = (
		frappe.get_cached_value(
			"Otto Task",
			perm["task"],
			"title",
		)
		or perm["task"]
	)

	message = (
		f"Permission requested to use tool <strong>{tool_title}</strong> "
		f"for task <strong>{task_title}</strong>"
	)
	if perm["target"] and perm["target_doctype"]:
		message += f" on target <strong>{perm['target_doctype']} - {perm['target']}</strong>"

	# Alert logs do not send emails
	# hence emails need to be manually sent
	log = otto.new(NotificationLog)
	log.for_user = user
	log.type = "Alert"
	log.document_type = "Otto Permission Request"
	log.document_name = perm["permission"]
	log.subject = f"Otto Permission Request - {tool_title} for task {task_title}"
	log.email_content = message
	log.insert(ignore_permissions=True)
	logger.debug(
		{
			"message": "notification logged",
			"user": user,
			"perm_req": perm["permission"],
			"assignments": assignments_str,
		}
	)

	try:
		eq = frappe.sendmail(
			recipients=[user],
			subject=log.subject,
			template="otto_permission_request",
			args={
				"message": message,
				"link": f"/app/otto-permission-request/{perm['permission']}",
			},
		)
		logger.debug(
			{
				"message": "email sent",
				"user": user,
				"perm_req": perm["permission"],
				"email_queue": eq.name if eq else None,
			}
		)
	except Exception:
		otto.log_error("error sending email", recipient=user)


@utils.cache(ttl=300)
def _skip_notification(user: str, perm_req: str):
	notifications_count = frappe.db.count(
		"Notification Log",
		filters={
			"for_user": user,
			"document_type": "Otto Permission Request",
			"document_name": perm_req,
		},
	)
	return notifications_count > 0
