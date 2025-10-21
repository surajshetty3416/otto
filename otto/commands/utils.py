import os
from pathlib import Path

import frappe


def init_site(site: str):
	frappe.init(site)
	frappe.connect()
	frappe.local.lang = frappe.get_system_settings("language")


def get_bench_root() -> Path | None:
	"""Returns the root directory of the bench"""
	current = Path(os.getcwd())

	while current != current.parent:
		if (current / "sites").exists() and (current / "apps").exists() and (current / "Procfile").exists():
			return current
		current = current.parent

	return None
