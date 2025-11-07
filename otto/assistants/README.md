# Assistant Definition Format

This document describes the assistant definition format. Assistants are AI agents with specific instructions, capabilities, and tools to accomplish tasks.

## Overview

Otto reads assistant definitions from either:

- **Single file assistants**: A single Python file containing the assistant definition. (eg. `my_assistant.py`)
- **Package assistants**: A Python package (directory with an `__init__.py` file) containing the assistant definition and optional helper modules.

Reference for the assistant definition format can be found in the `AssistantDefinition` type schema (see [`types.py`](./types.py)).

## Assistant Definition

When defining an assistant, the following variables may be defined:

```python
# Unique identifier for the Otto Assistant entry (used as the record key).
# It's recommended to follow the following format:
#   `{app_name}-{assistant_name}[-{version}]-assistant`
# whenever an assistant definition is synced, the uid is used to check existing
# records.
#
uid: str                                    # Name of the Otto Assistant entry


# Metadata that describes the assistant
#
name: str                                   # Human-readable title of the assistant
instruction: str = DEFAULT_INSTRUCTION      # System prompt to guide the assistant (supports Jinja template language)


# Tools available to the assistant
#
tools: ToolList = []                        # List of tools (see below for format options)
get_tools: Callable[[], ToolList] | None    # Function to dynamically load tools


# Model preferences
#
preferred_model: str | None = None                     # ID (substring) of the preferred model
preferred_config: ModelPreferenceConfig | None = None  # Preferred model configuration (size, reasoning, vision)
reasoning_effort: ReasoningEffort | None = None        # Default reasoning effort level


# Advanced features
#
get_context: Callable[[], dict[str, str]] | None = None  # Function to provide context for instruction templating
dev_mode_only: bool = False                              # Will not be installed if not in developer mode
```

> [!NOTE]
>
> When using a package assistant, the variables should be found in the `__init__.py` file.
> They don't need to be defined there but should be exported from the root `__init__.py` file.

### Tool List Format

The `tools` list can contain:

- **ToolDefinition objects**: Complete tool definitions (see [`otto.tools.types.ToolDefinition`](../tools/types.py))
- **Module path strings**: Dot-separated paths like `"otto.tools.bash_tool"` to modules that follow the `ToolDefinition` format
- **Module objects**: Already-imported tool modules that follow the `ToolDefinition` format

The `get_tools` function (if provided) returns the same format and will be called alongside the `tools` list to load tools dynamically.

## Simple Assistant Format

A simple assistant is defined in a single file. When using a single file, tools must be provided as `ToolDefinition` objects.

### Example: Simple Assistant

```python
# File: support_assistant.py

from otto.tools.utils import get_tool

uid = "app_name-support-assistant"
name = "Support Assistant"

instruction = """
You are a helpful customer support assistant.
Answer questions clearly and professionally.

You are talking to {{ user_name }}.
"""

def get_context():
  return { "user_name": frappe.session.user }

def search_tool(query: str): ...

def knowledge_tool(query: str): ...

# For single file assistants, use get_tool to load tool definitions
tools = [
    get_tool(search_tool, "app_name-search-tool"),
    get_tool(knowledge_tool, "app_name-knowledge-tool"),
]
```

Otto will use these attributes to create or update an Otto Assistant entry.

## Complex Assistant Format

Complex assistants are defined as Python packages (directories).

### Structure

For a complex assistant, create a package named `{name}_assistant/` with an `__init__.py` file that exports the assistant definition.

### Example: Complex Assistant

**Filesystem Structure**:

```
analytics_assistant/
├── __init__.py           # Assistant definition and exports
├── tools.py              # Dynamic tool loading logic
└── context.py            # Context provider for templating
```

```python
# File: analytics_assistant/__init__.py

from .tools import query_tool, analyze_tool

uid = "app_name-analytics-assistant"
name = "Analytics Assistant"

instruction = """
You are an analytics assistant for {{ company_name }}.
You have access to data up to {{ data_cutoff }}.
Help users understand their metrics and generate insights.
"""

# Dynamic tool loading
def get_tools():
  return [query_tool, analyze_tool]

# Context for instruction templating
def get_context():
  ...
  return {
    "company_name": company_name,
    "data_cutoff": cutoff,
  }

# Model preferences
preferred_model = "claude-sonnet-4-5"
preferred_config = {
    "size": "Medium",
    "is_reasoning": True,
    "supports_vision": False,
}
reasoning_effort = "Medium"
```

Helper modules:

```python
# File: analytics_assistant/tools.py

def query(query: str): ...
query_tool = get_tool(query, "app_name-query-tool")

def analyze(data: list[dict]): ...
analyze_tool = get_tool(analyze, "app_name-analyze-tool")
```

## How Assistants Are Read and Used

**Syncing assistants**: The [`sync_assistant`](./__init__.py) function is used
to sync assistant definitions to the database. This creates an app-defined
assistant that cannot be overridden by the user. They can alter it by
duplicating the assistant.

**Loading tools**: During sync, the `tools` list and `get_tools` function (if
provided) are used to load and sync all required tools. Tools are synced before
creating the assistant.

**Templating instructions**: If `get_context` is provided, it will be called
when the assistant is invoked to populate Jinja template variables in the
`instruction` string.

## Naming Guidelines

- For the definition file/package use descriptive names (e.g., `sales_assistant` or `customer_support_assistant`)
- For the `uid` use the following format: `{app_name}-{assistant_name}-assistant` (e.g., `otto-sales-assistant` or `my_app-support-assistant`)
- For the `name` use a human-readable title (e.g., `"Sales Assistant"` or `"Customer Support"`)

## Additional References

- See [`types.py`](./types.py) for the complete `AssistantDefinition` and `ModelPreferenceConfig` schemas
- See [`kitchen_sink/`](./kitchen_sink/) for a complete example assistant
- See [Tool Definition Format](../tools/README.md) for details on creating tools for assistants
- Refer to [`__init__.py`](./__init__.py) for the sync implementation
