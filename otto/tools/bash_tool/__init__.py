import os
from pathlib import Path
from textwrap import dedent

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

	# INSERT_YOUR_CODE
	# Check if we're on macOS (Darwin). If so, prepend bash command with sandbox-exec to prevent net access.

	if os.uname().sysname == "Darwin":
		profile_path = _get_sandbox_profile_path()
		command = f"sandbox-exec -f {profile_path} {command}"

	if os.uname().sysname != "Darwin":
		raise RuntimeError("Bash tool not yet implemented securely on non-macOS systems")

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


def _get_sandbox_profile_path() -> str:
	"""
	Saves and returns a sandbox profile string for macOS sandbox-exec that:
	- denies all network access,
	- allows file access only inside the bench root (excluding the `env` directory),
	- allows everything else by default.

	This profile is dynamically created using the bench root from get_bench_path.
	"""

	# this is a temp measure

	from frappe.utils import get_bench_path

	bench_root = Path(get_bench_path())
	profile_path = Path("/tmp") / "otto_bash_tool_sandbox_profile.sb"

	profile = dedent(f"""
		(version 1)

		(allow default)

		;; Deny all network access explicitly
		(deny network*)
		(deny file-write*)
		;; (deny file-read*) ;; make precise and enable

		;; Allow file reads, writes and execution within the allowed path
		(allow file-read* (subpath "{bench_root}"))
		(allow file-write* (subpath "{bench_root}/agents"))
		(allow process-exec (subpath "{bench_root}"))
		""")

	if not profile_path.exists() or profile_path.read_text() != profile:
		profile_path.write_text(profile)

	return profile_path.as_posix()
