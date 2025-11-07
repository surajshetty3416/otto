from frappe_mcp.server import ToolAnnotations

uid = "otto-bash-tool"
title = "Bash"

annotations = ToolAnnotations(
	readOnlyHint=False,
	destructiveHint=True,
	idempotentHint=False,
	openWorldHint=True,
	title=title,
)


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
