uid = "otto-bash-tool"
title = "Bash"

dev_mode_only = True
requires_permission = True
is_readonly = False
is_destructive = True
is_idempotent = False
is_open_world = True


def bash(command: str) -> str:
	"""
	Execute a bash command and return its standard output as a string.
	Raises an exception if the command fails.

	Args:
		command (str): The bash command to execute.

	Returns:
		str: The output from stdout of the command.
	"""
	# Make more secure maybe (even if dev mode only)
	# somehow ensure readonly access constrained to bench dir
	import subprocess

	from frappe.utils import get_bench_path

	result = subprocess.run(
		command,
		shell=True,
		capture_output=True,
		text=True,
		cwd=get_bench_path(),
	)

	if result.returncode != 0:
		raise RuntimeError(f"Command failed: {result.stderr.strip()}")

	return result.stdout.strip()
