from typing import TypedDict

import frappe


class Subject(TypedDict):
	# Target
	target: str | None
	target_doctype: str | None

	# DocType names
	task: str
	execution: str
	session: str
	permission: str
	tool: str | None

	# Values
	tool_use_id: str
	args: dict


def notify(perms: list[Subject]):
	"""Sends notification to all assigned users"""
	targets: list[tuple[str, str]] = list(
		set(
			(perm["target_doctype"], perm["target"])
			for perm in perms
			if perm["target"] and perm["target_doctype"]
		)
	)

	execs = list(set(perm["execution"] for perm in perms))
	sessions = list(set(perm["session"] for perm in perms))
	tasks = list(set(perm["task"] for perm in perms))
	tools = list(set(perm["tool"] for perm in perms if perm["tool"]))

	assigned_users = _get_assigned_users(
		targets=targets,
		tasks=tasks,
		tools=tools,
		executions=execs,
		sessions=sessions,
	)

	for perm in perms:
		target_assigned = assigned_users.get((perm["target_doctype"] or "", perm["target"] or ""), set())
		task_assigned = assigned_users.get(("Otto Task", perm["task"]), set())
		tool_assigned = assigned_users.get(("Otto Tool", perm["tool"] or ""), set())
		exec_assigned = assigned_users.get(("Otto Execution", perm["execution"]), set())
		session_assigned = assigned_users.get(("Otto Session", perm["session"]), set())
		assigned = target_assigned | task_assigned | tool_assigned | exec_assigned | session_assigned
		_send_notification(assigned, perm)


def _send_notification(assigned: set[str], subject: Subject): ...


def _get_assigned_users(
	targets: list[tuple[str, str]],
	tasks: list[str],
	tools: list[str],
	executions: list[str],
	sessions: list[str],
):
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
