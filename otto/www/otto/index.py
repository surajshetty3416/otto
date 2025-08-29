import frappe
from frappe.sessions import get_csrf_token


def get_context(context):
	context.site_name = frappe.conf.site_name
	context.csrf_token = get_csrf_token()
	context.is_dev_mode = "true" if frappe.conf.developer_mode else ""
