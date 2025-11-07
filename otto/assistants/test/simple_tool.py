"""Simple test tool for testing tool module references."""

uid = "test-simple-tool"
name = "simple_operation"


def simple_operation(x: int) -> int:
	"""
	Double the input number.

	Args:
		x (int): Number to double

	Returns:
		int: The doubled number
	"""
	return x * 2


# Alias for clarity - tools can use 'fn' or the function name
fn = simple_operation
