# Otto Lib

Library for adding LLM capabilities into Frappe apps.

> [!NOTE]
>
> Otto Lib is meant to be used specifically with Frappe apps. The library
> features offered by Otto are backed by DocTypes and so cannot be provided as a
> standalone library.

## Index

- [Examples](#examples)
  - [Quick one off query](#quick-one-off-query)
  - [Session based interaction](#session-based-interaction)
  - [Tool usage](#tool-usage)
  - [Model discovery and creation](#model-discovery-and-creation)
- [Installation](#installation)
- [Sessions](./session.md)
  - [Example](./sesssion.md#example)
  - [Reference](./sesssion.md#reference)
- [Models](./model.md)
  - [Example](./model.md#example)
  - [Reference](./model.md#reference)
- [Utilities](./utilities.md)

## Overview

If you're attempting to build LLM features into your Frappe app where:

- The user is given control over what models to choose, across multiple providers
- The user is allowed to update system prompts or instructions to better fit their need
- The user would like to track their LLM usage

Then Otto Lib is a suitable library to use. This library exposes Otto's core LLM
functionality allowing you to build custom LLM features around it.

Using this library allows Otto to manage:

1. [Sessions](./session.md):

   - Manage state of turn based or one shot LLM interactions.
   - Keep track of all LLM interactions.
   - View stats and analytics across all LLM interactions.

2. [Models](./model.md):
   - Use multiple model provders without having to deal with their individual APIs.
   - Use models that the user has access to.
   - Discover available models.

The library is sufficiently typed, with definitions exported from
[`otto.lib.types`](https://github.com/frappe/otto/blob/develop/otto/lib/types.py)
and defined in
[`otto.llm.types`](https://github.com/frappe/otto/blob/develop/otto/llm/types.py).

Otto uses this library internally for it's application level features, for example
[Otto Execution](https://github.com/frappe/otto/blob/develop/otto/otto/doctype/otto_execution/otto_execution.py).

> [!WARNING]
>
> For additional features, it is not recommended to directly access the
> underlying `OttoSession` DocType as this will change without any notice.
>
> If additional features are needed please open a [new issue](https://github.com/frappe/otto/issues/new).

## Examples

A few short examples that illustrate how Otto can be used:

- [Quick one off query](#quick-one-off-query)
- [Session based interaction](#session-based-interaction)
- [Tool usage](#tool-usage)
- [Model discovery and creation](#model-discovery-and-creation)

### Quick One-off Query

Quick one off query to summarize a document

```python
import otto.lib as otto
from otto.lib import content

# 1. Get model that matches criteria
model = otto.get_model(provider="Anthropic", size="Small")

# 2. Use model to summarize document
response = otto.quick_query(
    content.file(document_path, name="document.pdf"),
    model=model,
    instruction="Summarize the given document in 2 sentences.",
    stream=False,
)

# 3. Get content from response
print(response[0]["text"])
```

### Session-based Interaction

Session based interaction.

```python
import otto.lib as otto

# 1. Create session
session = otto.new(model="openai/gpt-4.1-mini", instruction="You are a helpful assistant")

# save session id to continue session later
session_id = session.id

# 2. Send user query to session
for chunk in session.interact("What's the weather like?"):
    print(chunk.get("text", ""), end="")
    stream_response(chunk)
```

Continue interaction with existing session.

```python
import otto.lib as otto

# 1. Load existing session
session = otto.load(session_id)

# 2. Continue interaction (without streaming)
response, _ = session.interact("What was my previous question?", stream=False)
print(response[0]["text"])
```

### Tool-usage

```python
import otto.lib as otto
from otto.lib.types import ToolUseUpdate, ToolSchema

# 1. Create session with tools
weather_tool = ToolSchema(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"]
    }
)
session = otto.new(model="openai/gpt-4.1", tools=[weather_tool])

# 2. Send user query and stream response
for chunk in session.interact("What's the weather in London?"):
    print(chunk.get("text", ""), end="")

# 3. Check and process pending tool calls
tool_updates: list[ToolUseUpdate] = []
for pending_tool in session.get_pending_tool_use():

    # Execute tool in you app
    result = execute_tool(
        name=pending_tool.name, # tool name eg: get_weather
        args=pending_tool.args, # tool args eg: {"location": "London"}
    )

    tool_update = ToolUseUpdate(
        id=pending_tool.id, # tool use id
        result=result,
    )
    tool_updates.append(tool_update)

# 4. Update session with tool call results
session.update_tool_use(tool_updates)

# 5. Continue session
for chunk in session.interact():
    print(chunk.get("text", ""), end="")
```

### Model discovery and creation

```python
import otto.lib as otto

# 1. Check availablilty
model = otto.is_model_available(model="gpt-4.1-mini")

# 2. Create new model if not available
model = otto.create_model(
    provider="Anthropic",
    name="gpt-4.1-mini",
    size="Small",
    is_reasoning=False,
    supports_vision=True,
)
otto.quick_query("...", model=model) # use created model

# 5. Model discovery
available_models = otto.get_models(is_reasoning=True, supports_vision=True)
```

## Installation

Otto is a Frappe application and to use Otto Lib, Otto needs to be installed
along side your Frappe application ([docs](https://docs.frappe.io/framework/user/en/guides/basics/apps#adding-app-to-a-site)).

```bash
# In your bench folder
bench get-app otto --branch develop

# Install the app on your site
bench --site site_name install-app otto
```

If you wish to make LLM features in your app available _as an option_, you can
check if it's available before using like so:

```python
try:
    import otto.lib as otto
except ImportError:
    otto = None


def llm_feature_in_your_app(...):
    if otto is None:
        return

    session = otto.new(...) # use session to implement feature
```

<!--
Point to implementation in other apps as example once done.
-->
