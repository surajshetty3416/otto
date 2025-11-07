from __future__ import annotations

import importlib
import inspect
import os
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeGuard

from frappe.utils import get_bench_path

if TYPE_CHECKING:
	from collections.abc import Callable
	from types import ModuleType


__all__ = [
	"get_import_path",
	"import_fn",
	"import_from_fs_path",
	"import_module",
	"is_dotted_path",
	"is_fs_path",
]


def get_import_path(fn: Callable) -> str:
	"""
	Get the import path for a function.

	If the function is in an app, then the import path is the dotted module path.
	The function can be regularly imported without loading the file.
		eg: otto.tools.bash_tool.bash

	If the function is not in an app, then the import path is the file path.
	The file must be loaded to import the function.
		eg: /home/user/projects/tools/package/bash_tool.py:bash


	Note: this function does not guarantee that the function will be imported
	from the same location, it saves the path of where the function is defined.
	"""
	fn_module = sys.modules.get(fn.__module__) or import_module(fn.__module__)
	fn_module_path = Path(inspect.getfile(fn_module))

	apps_path = Path(get_bench_path()).absolute() / "apps"

	with suppress(ValueError):
		if fn_module_path.is_relative_to(apps_path):
			module_path = fn_module_path.as_posix().removeprefix(apps_path.as_posix())
			module_path = module_path.replace(os.path.sep, ".")
			module_path = module_path.split(".", maxsplit=2)[2]
			module_path = module_path.removesuffix(".py").removesuffix("__init__").removesuffix(".")
			return f"{module_path}.{fn.__qualname__}"

	return f"{fn_module_path.as_posix()}:{fn.__qualname__}"


def import_fn(path: str) -> Callable:
	"""
	The argument `path` can be of the following forms:
	- dotted path: "path.to.module.function"
	- file path: "path/to/module.py:function"

	In both cases, module is first imported and then the function is returned
	from the module.
	"""

	parts = path.rsplit(":", maxsplit=1)
	if len(parts) != 2:
		parts = path.rsplit(".", maxsplit=1)

	if len(parts) != 2:
		raise ValueError(f"Invalid path provided: {path}")

	module_path, name = parts
	if not name.isidentifier():
		raise ValueError(f"Invalid function name found: {name} in path: {path}")

	module = import_module(module_path)
	fn = getattr(module, name, None)

	if fn is None:
		raise ValueError(f"Could not find function '{name}' in module '{module_path}'")

	if not callable(fn):
		raise ValueError(f"Imported attribute '{name}' from module '{module_path}' is not callable")

	return fn


def import_module(path: str) -> ModuleType:
	"""Imports module from dot separated path or file path"""

	if is_fs_path(path):
		return import_from_fs_path(path)

	if not is_dotted_path(path):
		raise ValueError(f"Invalid path provided: {path}")

	# Else import from dotted path
	return importlib.import_module(path)


def import_from_fs_path(path: str | Path) -> ModuleType:
	"""
	Provided path may be a path to a single file or to a package

	If provided path is to a package, then the module name is the name of the
	package (i.e. the name of the directory containing the __init__.py file)

	If provided path is to a single file, then the module name is the name of
	the file (i.e. the name of the file without the extension)

	If provided path is to a __init__.py file, then the module name will be then
	name its parent directory.
	"""

	if isinstance(path, str):
		path = Path(path)

	if not path.exists():
		raise FileNotFoundError(f"Incorrect path provided. File not found: {path}")

	#  Assume path is a directory to a package
	if path.is_dir():
		if not (path / "__init__.py").exists():
			raise ValueError(f"Invalid package path provided (__init__.py not found): {path}")

		parent = path.parent
		name = path.name

	# Assuming init file is from the package module root directory
	elif path.is_file() and path.name == "__init__.py":
		parent = path.parent.parent
		name = path.parent.name

	# Assuming file is a single file module
	elif path.is_file and path.name.endswith(".py"):
		parent = path.parent
		name = path.name.removesuffix(".py")

	else:
		raise ValueError(f"Invalid path provided: {path}")

	"""
	One of the ways this can go wrong is if the imported module has conflicting
	submodules. I.e. if the import writes to sys.modules such that some
	previously defined module is overwritten.

	This can't be prevented by using importlib.util.spec_from_file_location
	because and then loading the module from spec and executing it. This is
	cause even if the module is loaded in such a way, for complex_modules
	(having submodules) the sys.modules will still have to be updated. Else the
	module won't exec.

	So this brittleness feels a bit unavoidable, only way to alleviate this is
	to make sure that external modules have unique names and to be circumspect
	when importing external modules.
	"""

	sys.path.insert(0, parent.as_posix())
	try:
		return importlib.import_module(name)
	finally:
		sys.path.pop(0)


def is_fs_path(path: Any) -> TypeGuard[str]:
	import os

	if not isinstance(path, str) or not path:
		return False

	if os.path.sep in path or (os.path.altsep and os.path.altsep in path):
		return True
	if os.path.isabs(path):
		return True
	if os.path.exists(path):
		return True

	return False


def is_dotted_path(path: Any) -> TypeGuard[str]:
	"""
	Check if the provided path is a Python module path (dot separated and valid Python identifiers).
	"""
	if not isinstance(path, str) or not path:
		return False

	parts = path.split(".")
	for part in parts:
		if not part.isidentifier():
			return False
	return len(parts) > 1
