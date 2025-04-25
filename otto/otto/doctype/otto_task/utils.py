import importlib

import frappe
import frappe.utils.logger

HANDLER_PATH = "otto.otto.doctype.otto_task.otto_task.handler"
START_MARKER = "# __START_DOC_EVENTS__"
END_MARKER = "# __END_DOC_EVENTS__"


def logger(name: str):
	frappe.utils.logger.set_log_level("INFO")
	return frappe.logger(name)


def update_doc_events(doctype: str, event: str, remove: bool = False):
	doc_events = frappe.get_hooks("doc_events", app_name="otto")
	handlers = doc_events.setdefault(doctype, {}).setdefault(event, [])
	if isinstance(handlers, str):
		handlers = [handlers]

	if remove:
		handlers = [h for h in handlers if h != HANDLER_PATH]
	elif HANDLER_PATH in handlers:
		return
	else:
		handlers.append(HANDLER_PATH)

	doc_events[doctype][event] = handlers
	if not handlers:
		del doc_events[doctype][event]

	if not doc_events[doctype]:
		del doc_events[doctype]

	update_hooks(doc_events)
	clear_hooks_cache()


def update_hooks(doctype_events: dict):
	hooks_path = frappe.get_app_path("otto", "hooks.py")

	try:
		with open(hooks_path) as f:
			lines = f.readlines()
	except FileNotFoundError:
		logger("otto.utils").error(f"hooks.py not found at {hooks_path}")
		return

	start_index = -1
	end_index = -1

	for i, line in enumerate(lines):
		if line.strip() == START_MARKER:
			start_index = i
		elif line.strip() == END_MARKER:
			end_index = i
			break

	if start_index == -1 or end_index == -1:
		logger("otto.utils").error(f"Markers not found in {hooks_path}")
		return

	# Keep existing indentation of the start marker line for the generated content
	start_line = lines[start_index]
	indentation = start_line[: start_line.find(START_MARKER)]

	# Format the new doc_events content
	new_doc_events_str = format_hooks_dict(doctype_events)
	# Indent the generated string to match the start marker's indentation
	indented_new_doc_events_str = "\n".join([indentation + line for line in new_doc_events_str.splitlines()])

	# Construct the new content
	new_lines = lines[: start_index + 1] + [indented_new_doc_events_str + "\n"] + lines[end_index:]

	try:
		with open(hooks_path, "w") as f:
			f.writelines(new_lines)
		logger("otto.utils").info(f"Updated hooks in {hooks_path}")
	except OSError as e:
		logger("otto.utils").error(f"Failed to write to {hooks_path}: {e}")


def format_hooks_dict(data: dict[str, dict[str, list[str]]]) -> str:
	"""Formats the doctype_events dictionary into a string for hooks.py."""
	lines = ["doc_events = {"]
	tab = "\t"
	for doctype, events in sorted(data.items()):
		if not events:
			continue
		lines.append(f"{tab}{repr(doctype)}: {{")
		for event, handlers in sorted(events.items()):
			if not handlers:
				continue
			lines.append(f"{tab * 2}{repr(event)}: [")
			# Ensure handlers is always a list, even if originally a string
			handler_list = handlers if isinstance(handlers, list) else [handlers]
			for handler in sorted(handler_list):
				lines.append(f"{tab * 3}{repr(handler)},")
			lines.append(f"{tab * 2}],")
		# Remove trailing comma from the last event entry if needed
		if lines[-1].endswith(","):
			lines[-1] = lines[-1][:-1]
		lines.append(f"{tab}}},")
	# Remove trailing comma from the last doctype entry if needed
	if lines[-1].endswith(","):
		lines[-1] = lines[-1][:-1]

	lines.append("}")
	return "\n".join(lines)


def clear_hooks_cache():
	if hasattr(frappe.local, "doc_events_hooks"):
		delattr(frappe.local, "doc_events_hooks")

	if frappe.client_cache and frappe.client_cache.get_value("app_hooks"):
		frappe.client_cache.delete_value("app_hooks")

	hooks = frappe.get_module("otto.hooks")
	importlib.reload(hooks)
