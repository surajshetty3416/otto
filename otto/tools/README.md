# Tool Definition Format

This document describes the tool definition format. Tools are callable functions
that can be invoked to perform specific actions or retrieve information.

## Overview

Otto reads tool definitions from either:

- **Single file tools**: A single Python file containing the tool definition and implementation. (eg. [`bash_tool.py`](./bash_tool.py))
- **Package tools**: A Python package (directory with an `__init__.py` file) containing the tool definition and implementation across multiple files.

Reference for the tool definition format can be found in the `ToolDefinition` type schema (see [`types.py`](./types.py)).

## Tool Tool Definition

When defining a tool, the following variables may be defined:

```python
# Unique identifier for the Otto Tool entry (used as the record key).  It's
# recommended to follow the following format:
#   `{app_name}-{tool_name}[-{version}]-tool`
# whenever a tool definition is synced, the uid is used to check existing
# records.
#
uid: str                                    # Name of the Otto Tool entry


# Metadata that is used to give context to the LLM about the tool these can be
# inferred from the tool file/folder name, annotation and docstring
#
name: str                                   # Tool name (internal and LLM-facing)
title: str                                  # Human-readable name
description: str                            # Tool summary for users and LLMs
properties: dict[str, Any]                  # Arguments schema
required: list[str]                         # Required parameters


# Implementation of the tool
#
fn: Callable                                # The Python function implementing the tool


# Flags that define how the tool is installed/used
#
dev_mode_only: bool = False                 # Will not be installed if not in developer mode
requires_permission: bool = False           # Will raise an Otto Permission Request before execution
use_explanation: bool = False               # Will prompt LLM for explanation for using the tool


# Optional definitions described by the MCP spec
#
output_properties: dict[str, Any] | None = None # Optional output schema
output_required: list[str] | None = None        # Optional required output fields
annotations: ToolAnnotations | None = None      # Optional MCP metadata
```

> [!NOTE]
>
> When using a package tool, the variable should be found in the `__init__.py` file.
> They don't need to be defined there but should be exported from the root `__init__.py` file.

Some fields that are not explicitly defined can be inferred from the definition file:

- **`name`**: Inferred from the file name (e.g., `search_tool.py` → `search`)
- **`fn`**: Inferred from a function matching `name` in the module
- **`description`**: Extracted from the function's docstring
- **`title`**: Capitalized version of `name` (e.g., `search` → `Search`)
- **`properties`**: Inferred from function type annotations and docstring
- **`required`**: Inferred from function signature (parameters without defaults)

## Simple Tool Format

A simple tool is defined in a single file named `{name}_tool.py`.

### Example: Simple Tool

```python
# File: greet_tool.py

uid = "app_name-greet-tool"

def greet(name: str, greeting: str = "Hello") -> str:
    """
    Greet a person with a custom greeting.

    Args:
        name: The person's name
        greeting: The greeting to use

    Returns:
        A greeting message
    """
    return f"{greeting}, {name}!"
```

Otto will automatically infer:

- `name`: `greet`
- `title`: `"Greet"`
- `description`: "Greet a person with a custom greeting."
- `properties`: Inferred from type hints and docstring
- `required`: `["name"]` (since `greeting` has a default)
- `fn`: The `greet` function

## Complex Tool Format

Complex tools are defined as Python packages (directories).

### Structure

For a complex tool, create a package named `{name}_tool/` with an `__init__.py` file that exports the tool definition.

### Example: Complex Tool

**Filesystem Structure**:

```
weather_tool/
├── __init__.py           # Tool definition and exports
├── api_client.py         # Helper module for API calls
└── parsers.py            # Helper module for parsing responses
```

```python
# File: weather_tool/__init__.py

from .api_client import fetch_weather_data
from .parsers import parse_weather_response

uid = "app_name-weather-tool"

def weather(location: str, units: str = "metric") -> dict:
    """
    Get current weather information for a location.

    Args:
        location: City name or coordinates
        units: Temperature units (metric/imperial)

    Returns:
        Weather data including temperature, conditions, and humidity
    """
    raw_data = fetch_weather_data(location, units)
    return parse_weather_response(raw_data)
```

Additional code required by the tool function:

```python
# File: weather_tool/api_client.py
def fetch_weather_data(location: str, units: str) -> dict: ...

# File: weather_tool/parsers.py
def parse_weather_response(data: dict) -> dict: ...
```

## How Tools Are Read and Used

**Syncing tools**: the [`sync_tool`](./__init__) function is used to sync tool
*definitions to the database. This creates and app defined tool that cannot be
*overridden by the user. They can alter it by duplicating the tool.

**Invoking the tools**: a path to the tool is stored in the `Otto Tool` entry of
the tool. When executing the tool, this path is used to import and run the tool.
Due to this the source code of the tool is needed and cannot be discarded after
syncing.

## Naming Guidelines

- For the definition file/package use descriptive, specific names (e.g., `company_weather_tool` instead of `weather_tool`) to avoid conflicts with standard library modules
- For the `uid` use the following format: `{app_name}-{tool_name}[-{version}]-tool` (eg. `otto-weather-tool` or `otto-weather-1.0.0-tool`)

## Additional References

- See [`types.py`](./types.py) for the complete `ToolDefinition` schema
- See existing tools in the [`otto/tools/`](./) directory for examples
- Refer to the [Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-06-18/schema#tool) for properties and annotation formats
