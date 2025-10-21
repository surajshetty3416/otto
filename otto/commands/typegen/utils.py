import os
from pathlib import Path

import click


def get_tags(tag: str):
	start_tag = f"// <{tag}>"
	end_tag = f"// </{tag}>"
	return start_tag, end_tag


def clear_types(tag: str, out_path: Path):
	start_tag, end_tag = get_tags(tag)

	if not out_path.exists():
		return False

	with open(out_path, "r") as f:
		file_content = f.read()

	start_idx = file_content.find(start_tag)
	end_idx = file_content.find(end_tag)

	if start_idx == -1 or end_idx == -1:
		# Tags not found, nothing to clear
		return False

	# Replace content between tags with just the tags
	end_idx += len(end_tag)
	new_content = file_content[:start_idx] + start_tag + "\n" + end_tag + file_content[end_idx:]

	with open(out_path, "w") as f:
		f.write(new_content)

	return True


def save_types(types: str, tag: str, out_path: Path) -> bool:
	start_tag, end_tag = get_tags(tag)

	content = "\n".join(
		[
			start_tag,
			"// Auto-generated using `bench generate-types`. Do not edit.",
			"",
			types.strip(),
			end_tag,
		]
	)

	if not out_path.exists():
		with open(out_path, "w") as f:
			f.write(content)
		return True

	with open(out_path, "r") as f:
		file_content = f.read()

	start_idx = file_content.find(start_tag)
	end_idx = file_content.find(end_tag)

	if start_idx == -1 or end_idx == -1:
		# Tags not found, append content
		with open(out_path, "a") as f:
			f.write("\n\n" + content)
		return True

	# Replace content between tags
	end_idx += len(end_tag)
	new_content = file_content[:start_idx] + content + file_content[end_idx:]
	with open(out_path, "w") as f:
		f.write(new_content)

	return True


def get_out_path(app: str, out: str) -> Path | None:
	from otto.commands.utils import get_bench_root

	if not (bench_root := get_bench_root()):
		return print(click.style(f"Error: Bench root not found from {os.getcwd()}", fg="red"))
	return bench_root / "apps" / app / out
