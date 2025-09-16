from typing import TypedDict

import frappe

import otto
from otto.utils import to_html


class Subject(TypedDict):
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


def notify(perms: list[Subject]):
	"""Sends notification to all assigned users for tool use request"""

	assigned_users = _get_assigned_users(perms)
	assigned_users_map: dict[str, list[Subject]] = {}

	for perm in perms:
		target_assigned = assigned_users.get((perm["target_doctype"] or "", perm["target"] or ""), set())
		task_assigned = assigned_users.get(("Otto Task", perm["task"]), set())
		tool_assigned = assigned_users.get(("Otto Tool", perm["tool"] or ""), set())
		exec_assigned = assigned_users.get(("Otto Execution", perm["execution"]), set())
		session_assigned = assigned_users.get(("Otto Session", perm["session"]), set())
		assigned = target_assigned | task_assigned | tool_assigned | exec_assigned | session_assigned

		for user in assigned:
			assigned_users_map.setdefault(user, []).append(perm)
		# _send_notification(assigned, perm)

	for user, perms in assigned_users_map.items():
		_create_notification_logs(user, perms)


def _get_assigned_users(
	perms: list[Subject],
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

	for target, target_doctype in targets:
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

	assignment_map: dict[tuple[str, str], set[str]] = {}
	for user in assigned_users:
		assignment_map.setdefault((user.reference_type, user.reference_name), set()).add(user.allocated_to)

	return assignment_map


def _create_notification_logs(user: str, perms: list[Subject]):
	"""Create single notification log for each tool use request"""

	tool_map: dict[str, list[Subject]] = {}
	for perm in perms:
		tool_map.setdefault(perm["tool_use_id"], []).append(perm)

	for _, perms in tool_map.items():
		_notify(user, perms)


def _notify(user: str, perm: list[Subject]):
	from frappe.desk.doctype.notification_log.notification_log import NotificationLog

	subject = Subject(**perm[0])
	for p in perm:
		for key, value in p.items():
			if not subject.get(key):
				subject[key] = value

	tool_title = subject["tool_slug"]
	if subject["tool"]:
		tool_title = (
			frappe.get_cached_value(
				"Otto Tool",
				subject["tool"],
				"title",
			)
			or subject["tool_slug"]
		)
	task_title = (
		frappe.get_cached_value(
			"Otto Task",
			subject["task"],
			"title",
		)
		or subject["task"]
	)

	message = (
		f"Permission requested to use tool <strong>{tool_title}</strong> "
		f"for task <strong>{task_title}</strong>"
	)
	if subject["target"] and subject["target_doctype"]:
		message += f" on target <strong>{subject['target_doctype']} - {subject['target']}</strong>"

	# Alert logs do not send emails
	# hence emails need to be manually sent
	log = otto.new(NotificationLog)
	log.for_user = user
	log.type = "Alert"
	log.document_type = "Otto Permission Request"
	log.document_name = subject["permission"]
	log.subject = f"Otto Permission Request - {tool_title} for task {task_title}"
	log.email_content = to_html(message)
	log.insert(ignore_permissions=True)

	frappe.sendmail(
		recipients=[user],
		subject=log.subject,
		template="otto_permission_request",
		args={
			"message": message,
			"link": f"/app/otto-permission-request/{subject['permission']}",
		},
	)
