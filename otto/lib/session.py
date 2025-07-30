"""
Library wrapper around OttoSession
"""

from otto.llm.types import ToolUseUpdate


class SessionManager:
	def save(self): ...

	def interact(self): ...

	def get_called_tools(self):
		"""Return dict of tool_name: (args, env_str) of the last item"""
		...

	def update_tool_results(self):
		"""Updates tool results for the given items"""
		...


def new() -> SessionManager: ...


def load(name: str): ...


def interact(): ...


def execute_tool(func, args, kwargs) -> ToolUseUpdate: ...
