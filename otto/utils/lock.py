from __future__ import annotations

import contextlib
import hashlib
from typing import TYPE_CHECKING

import frappe
from frappe.utils.file_lock import LockTimeoutError
from frappe.utils.synchronization import filelock

if TYPE_CHECKING:
	from frappe.model.document import Document


@contextlib.contextmanager
def lock_doc(doc: Document, *, lock_name: str, timeout: int = 600):
	"""
	Lock doc is used to lock critical sections of a document.

	The reason for not using `doc.lock` directly is to prevent
	frappe.DocumentLockedError from being raised when saving the locked
	document.
	"""
	signature = _get_lock_signature(doc, lock_name=lock_name)

	try:
		with filelock(signature, timeout=timeout):
			yield
	except LockTimeoutError as e:
		raise frappe.DocumentLockedError from e


def _get_lock_signature(doc: Document, *, lock_name: str):
	return hashlib.sha224(
		f"Otto::{doc.doctype}:{doc.name}:{lock_name}".encode(),
		usedforsecurity=False,
	).hexdigest()
