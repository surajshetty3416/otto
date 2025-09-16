from typing import Literal

import frappe

import otto


@frappe.whitelist(methods=["POST"])
def acknowledge(
	name: str,
	type: Literal["grant", "deny"],
	override_args: dict | None = None,
):
	from otto.otto.doctype.otto_permission_request.otto_permission_request import OttoPermissionRequest

	if not name or type not in ["grant", "deny"]:
		return

	status = "Granted" if type == "grant" else "Denied"

	otto.get(OttoPermissionRequest, name).acknowledge(
		status,
		override_args,
	)
