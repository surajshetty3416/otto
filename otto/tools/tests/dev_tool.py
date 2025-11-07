"""Test tool with dev_mode_only for testing sync_tool function."""

uid = "test-tools-dev"
title = "Dev Only Tool"
name = "dev_operation"
dev_mode_only = True


def dev_operation(data: str) -> str:
	"""
	A development-only operation.

	Args:
		data (str): Input data

	Returns:
		str: Processed data
	"""
	return f"DEV: {data}"
