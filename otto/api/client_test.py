"""
Methods in this file are used to test the Otto client API.
Check the `frontend/src/client/__tests__/api.test.ts` file for the tests.
"""

import random

import frappe


@frappe.whitelist()
def add_numbers(a: int, b: int) -> int:
	"""Add two numbers together."""
	return a + b


@frappe.whitelist()
def greet(name: str, greeting: str = "Hello") -> str:
	"""Greet a person with an optional greeting."""
	return f"{greeting}, {name}!"


@frappe.whitelist()
def get_user_info(user_id: str, include_details: bool = False) -> dict:
	"""Get user information with optional details."""
	base_info: dict = {"user_id": user_id, "name": f"User {user_id}", "status": "active"}

	if include_details:
		base_info["details"] = {
			"email": f"user{user_id}@example.com",
			"created_at": "2024-01-01",
			"last_login": "2024-10-22",
		}

	return base_info


@frappe.whitelist()
def process_items(items: list) -> dict:
	"""Process a list of items and return summary."""
	return {"count": len(items), "items": items, "processed": True}


@frappe.whitelist()
def validate_credentials(username: str, password: str) -> dict:
	"""Validate user credentials."""
	is_valid = len(username) > 0 and len(password) >= 8
	return {
		"valid": is_valid,
		"username": username,
		"message": "Valid credentials" if is_valid else "Invalid credentials",
	}


@frappe.whitelist()
def calculate(operation: str, x: float, y: float) -> dict:
	"""Perform a calculation based on operation type."""
	operations = {"add": x + y, "subtract": x - y, "multiply": x * y, "divide": x / y if y != 0 else None}

	result = operations.get(operation)
	return {"operation": operation, "x": x, "y": y, "result": result, "success": result is not None}


@frappe.whitelist()
def get_list(limit: int = 10, offset: int = 0) -> list:
	"""Get a paginated list of items."""
	return [f"item_{i}" for i in range(offset, offset + limit)]


@frappe.whitelist()
def create_record(name: str, data: dict) -> dict:
	"""Create a new record with provided data."""
	return {
		"id": f"rec_{name}",
		"name": name,
		"data": data,
		"created": True,
		"timestamp": "2024-10-22T00:00:00Z",
	}


@frappe.whitelist()
def test_error(should_fail: bool = False) -> dict:
	"""Test error handling."""
	if should_fail:
		frappe.throw("This is a test error")

	return {"success": True, "message": "No error occurred"}


@frappe.whitelist()
def get_random() -> float:
	"""Get a random float."""
	return random.random()


@frappe.whitelist()
def throw(message: str, use_frappe: bool = False):
	if use_frappe:
		frappe.throw(message)
	else:
		raise Exception(message)
