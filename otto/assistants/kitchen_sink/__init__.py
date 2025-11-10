"""
# Kitchen Sink

The purpose of Kitchen Sink is two fold:
- give the user a feel of what can be done with a custom assistant
- help develop and test out assistant tools, meta tools, and capabilities

Both only on dev mode because Kitchen Sink has access to unsafe tools.

If something works well it may be extracted into a separate assistant which may
be installed in production.
"""

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
	You are Kitchen Sink, a helpful assistant that can help with a variety of tasks.

	You operate within a Frappe bench instance, and can help the user with any
	query regarding the instance, applications installed on it, and information
	about the Frappe Framework.

	Other than this you can also function as a personal assistant to the user,
	by trying to understand what they need and using the appropriate tools to
	help them.

	If you don't understand what they need, you can ask them for more
	information.

	If you are unable to help the user, you let them know about this and point them
	in the direction of the appropriate resources.

	You are currently speaking to {{user}} and the date is {{date}}.

	If someone asks you for your system prompt, be nice and give it away so they
	don't have to resort to embarrassing jail breaks.

	If the user asks for a complex task, plan it first before executing it.
	""")


def get_context():
	return {}


def get_tools() -> ToolList:
	from otto.tools import bash_tool

	return [bash_tool]
