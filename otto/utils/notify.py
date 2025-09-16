from typing import TypedDict

import frappe

import otto


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
		_create_notification_log(user, perms)


def _create_notification_log(user: str, perm: list[Subject]):
	from frappe.desk.doctype.notification_log.notification_log import NotificationLog

	subject = Subject(**perm[0])
	for p in perm:
		for key, value in p.items():
			if not subject.get(key):
				subject[key] = value

	log = otto.new(NotificationLog)
	log.for_user = user
	log.type = ""  # Alert notifications are not sent via email

	log.document_type = "Otto Permission Request"
	log.document_name = subject["permission"]

	tool_title = subject["tool_slug"]
	if subject["tool"]:
		tool_title = frappe.get_cached_value("Otto Tool", subject["tool"], "title") or subject["tool_slug"]
	task_title = frappe.get_cached_value("Otto Task", subject["task"], "title") or subject["task"]

	log.subject = f"Permission required to use tool <strong>{tool_title}</strong> for task <strong>{task_title}</strong>"
	# if subject["target"] and subject["target_doctype"]:
	# 	log.subject += f" on target <strong>{subject['target_doctype']} - {subject['target']}</strong>"

	log.email_content = _get_email_content(
		subject=subject,
		task_title=task_title,
		tool_title=tool_title,
	)

	log.insert(ignore_permissions=True)


def _get_email_content(
	*,
	subject: Subject,
	task_title: str | None,
	tool_title: str,
) -> str:
	from frappe.utils import escape_html, get_url

	from otto.utils import to_html

	base_url = get_url()
	if subject["tool"]:
		message = (
			f"Permission required to use tool **[{tool_title}]({base_url}/app/otto-tool/{subject['tool']}])** "
			f"for task **[{task_title}]({base_url}/app/otto-task/{subject['task']})**"
		)
	else:
		message = (
			f"Permission required to use tool **{tool_title}** "
			f"for task **[{task_title}]({base_url}/app/otto-task/{subject['task']})**"
		)

	if subject["target"] and subject["target_doctype"]:
		doc_slug = subject["target_doctype"].lower().replace(" ", "-")
		target_url = f"{base_url}/app/{doc_slug}/{subject['target']}"
		message += f" on target **[{subject['target_doctype']} - {subject['target']}]({target_url})**"

	req_url = f"{base_url}/app/otto-permission-request/{subject['permission']}"
	md_parts = [
		message,
		"",
		f"[Click here to view permission request]({req_url})",
		"",
		"---",
		"",
	]

	args = subject["tool_args"].items()

	if len(args) > 0:
		md_parts.extend(
			[
				"### Tool Arguments",
				"",
			]
		)
	for name, value in args:
		if name == "explanation":
			continue

		md_parts.extend(
			[
				f"**{name.replace('_', ' ').title()}:**",
				f"```markdown\n{escape_html(value)}\n```",
				"",
			]
		)

	if explanation := subject["tool_args"].get("explanation"):
		md_parts.extend(
			[
				f"_**Usage reason:** {escape_html(explanation)}_",
				"",
			]
		)

	md_parts.append(
		f"[View Session]({base_url}app/view-otto-session/{subject['session']})",
	)

	md_content = "\n\n".join(md_parts)
	return to_html(md_content)
