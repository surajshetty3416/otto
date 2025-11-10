from __future__ import annotations

from typing import TYPE_CHECKING

from otto.assistants.types import ModelPreferenceConfig
from otto.utils import format_prompt as f

if TYPE_CHECKING:
	from otto.assistants.types import ToolList

uid = "otto-kitchen-sink"
name = "Kitchen Sink"
dev_mode_only = True

# Model preferences
preferred_model = "claude-sonnet-4-5"
preferred_config = ModelPreferenceConfig(
	size="Medium",
	is_reasoning=True,
	supports_vision=True,
)
reasoning_effort = "Medium"

instruction = f("""
	You are a helpful assistant that can help with a variety of tasks.

	You are currently speaking to {{user}} and the date is {{date}}.
	""")


def get_context():
	return {}


def get_tools() -> ToolList:
	from otto.tools import bash_tool

	return [bash_tool]
