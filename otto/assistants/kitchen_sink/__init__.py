from __future__ import annotations

from otto.assistants.kitchen_sink.tools import bash_tool
from otto.assistants.types import AssistantTool, ModelPreferenceConfig
from otto.utils import format_prompt as f

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


tools: list[AssistantTool] = [bash_tool]
