import importlib
import os
from re import U

import frappe
import frappe.utils.logger


def logger(name: str):
	frappe.utils.logger.set_log_level("INFO")
	return frappe.logger(name)
