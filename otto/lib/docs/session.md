# Sessions

High-level LLM interaction state management.

Sessions management in Otto is backed by the `OttoSession` DocType. This keeps
track of the session state and configuration such as model, instruction,
reasoning effort, and tools used in the session. All of these may be updated mid
interaction. All changes made here will be reflected in the respective DocType.

To see how `Session` is used by Otto you may view the [Otto Execution
source](https://github.com/frappe/otto/blob/develop/otto/otto/doctype/otto_execution/otto_execution.py).

- [Example](#example)
- [Reference](#reference)

## Example

A short example that illustrates how session may be used.

```python
import otto.lib as otto

# Create new session
session = otto.new(
    model="anthropic/claude-3-5-sonnet-20241022",
    instruction="You are a helpful coding assistant",
    tools=[calculator_tool_schema],
)

# Interact (streaming)
stream = session.interact("Calculate 15 * 23", stream=True)
for chunk in stream:
    print(chunk.get("text", ""), end="")
result = stream.item

# Handle tool use
pending_tools = session.get_pending_tool_use()
for tool in pending_tools:
    result = execute_tool(tool.name, tool.args)
    session.update_tool_use(ToolUseUpdate(id=tool.id, status="success", result=result))

# Continue conversation (non-streaming)
response, _ = session.interact("What was the result?", stream=False)
if response:
    print(response["content"])
```

## Reference

- [`new`](#new): Create a new session.
- [`load`](#load): Load a session from a DocType.
- [`Session`](#session): Class for managing LLM interaction state.
  - [`Session.interact`](#sessioninteract): Perform one turn of interaction with the LLM.
  - [`Session.get_pending_tool_use`](#sessionget_pending_tool_use): Retrieve tool use requests that are pending execution after an LLM response.
  - [`Session.update_tool_use`](#sessionupdate_tool_use): Update the status and result of tool use requests within the session after execution.
  - [`Session.get_last_item`](#sessionget_last_item): Returns the most recent item from the session's interaction history (user message, agent response, or tool result).
  - [`Session.get_last_response`](#sessionget_last_response): Returns the last agent response from the session.
  - [Miscellaneous](#miscellaneous): Other properties and methods.
- [`quick_query`](#quick_query): Convenience function for one-off LLM queries without session management.

> [!TIP]
>
> It is recommended to view the source code
> ([ref](https://github.com/frappe/otto/blob/develop/otto/lib/session.py)) for
> the methods or functions that you need to use as it is well documented.
>
> Since most functions and methods are well typed, you can use your IDE's view
> definition feature to get accurate info on the signature and return types.
>
> Type definitions are in
> [otto.lib.types](https://github.com/frappe/otto/blob/develop/otto/lib/types.py)
> and
> [otto.llm.types](https://github.com/frappe/otto/blob/develop/otto/llm/types.py).

### `new`

Creates a new LLM session with the specified configuration.

```python
def new(
    model: str = utils.DEFAULT_MODEL,
    instruction: str = utils.DEFAULT_INSTRUCTION,
    reasoning_effort: ReasoningEffort | None = None,
    tools: list[ToolSchema] | None = None,
) -> Session
```

**Example:**

```python
import otto.lib as otto

session = otto.new(
    model="anthropic/claude-3-5-sonnet-20241022",
    instruction="You are a helpful assistant",
    reasoning_effort="Medium",
    tools=[calculator_tool_schema]
)
```

### `load`

Loads an existing LLM session from the database using its unique identifier.

```python
def load(id: str) -> Session
```

**Example:**

```python
import otto.lib as otto

# Load an existing session
session = otto.load("session-12345")
print(f"Loaded session with model: {session.model}")
```

### `Session`

The main class for managing LLM interaction state. Provides a high-level wrapper around the `OttoSession` DocType.

**Properties:**

- `id`: Session identifier
- `model`: LLM model being used
- `instruction`: System instruction/prompt
- `reasoning_effort`: Reasoning effort level
- `tools`: Available tools
- `is_active`: Whether session is currently processing a query
- `failure_reason`: Reason for failure if any

#### `Session.interact`

Performs one turn of interaction with the LLM. Sends the query along with session context to the LLM and updates the session with the response.

```python
def interact(
    self,
    query: Query | None = None,
    *,
    stream: bool = True,
) -> InteractStreamResponse | InteractResponse
```

**Example:**

```python
# Streaming interaction
stream = session.interact("What is 2 + 2?", stream=True)
for chunk in stream:
    print(chunk.get("content", ""), end="")
result = stream.item

# Non-streaming interaction
response, reason = session.interact("Hello there", stream=False)
if response:
    print(response["content"])
```

#### `Session.get_pending_tool_use`

Retrieves tool use requests that are pending execution after an LLM response.

```python
def get_pending_tool_use(self, last_item_only: bool = True) -> list[PendingToolUse]
```

**Example:**

```python
# After an interact() call that requests tools
pending_tools = session.get_pending_tool_use()
for tool in pending_tools:
    print(f"Tool: {tool.name}, Args: {tool.args}")
    # Execute the tool...
    result = execute_calculator(tool.args)
    session.update_tool_use(ToolUseUpdate(id=tool.id, result=result))
```

#### `Session.update_tool_use`

Updates the status and result of tool use requests within the session after execution.

```python
def update_tool_use(self, update: ToolUseUpdate | list[ToolUseUpdate]) -> None
```

**Example:**

```python
from otto.lib.types import ToolUseUpdate

# Update a single tool use
session.update_tool_use(ToolUseUpdate(
    id="tool_12345",
    result="The calculation result is 42",
    start_time=time.time(),
    end_time=time.time() + 1,
))

# Update multiple tool uses
updates = [
    ToolUseUpdate(id="tool_1", result="Result 1"),
    ToolUseUpdate(id="tool_2", result="Result 2"),
]
session.update_tool_use(updates)
```

#### `Session.get_last_item`

Returns the most recent item from the session's interaction history (user message, agent response, or tool result).

```python
def get_last_item(self) -> SessionItem | None
```

**Example:**

```python
last_item = session.get_last_item()
if last_item:
    print(f"Last item role: {last_item['meta']['role']}")
    print(f"Content: {last_item['content']}")
```

#### `Session.get_last_response`

Returns the last agent response from the session. Returns `None` if the last item is not an agent response.

```python
def get_last_response(self) -> list[Content] | None
```

**Example:**

```python
last_response = session.get_last_response()
if last_response:
    for content in last_response:
        if content["type"] == "text":
            print(f"Agent said: {content['text']}")
```

#### Miscellaneous

The Session class provides properties for accessing and modifying session configuration:

**Model:**

```python
# Get current model
current_model = session.model

# Set new model
session.set_model("anthropic/claude-3-haiku-20240307")
```

**Instruction:**

```python
# Get current instruction
instruction = session.instruction

# Set new instruction
session.set_instruction("You are a coding assistant specialized in Python")
```

**Reasoning Effort:**

```python
# Get current reasoning effort
effort = session.reasoning_effort

# Set reasoning effort
session.set_reasoning_effort("High")
```

**Tools:**

```python
# Get current tools
tools = session.tools

# Set new tools
session.set_tools([calculator_tool, file_reader_tool])
```

**Other Properties:**

```python
# Read-only properties
session_id = session.id # Name of the Otto Session DocType
is_processing = session.is_active # True if session.interact is running
error_reason = session.failure_reason # Set if error occurs in session.interact

# Get session statistics
stats = session.get_stats()
call_count = session.get_llm_call_count()
```

### `quick_query`

Convenience function for one-off queries without manual session management. Creates a new session and immediately interacts with it.

```python
def quick_query(
    query: Query,
    *,
    model: str = utils.DEFAULT_MODEL,
    instruction: str = utils.DEFAULT_INSTRUCTION,
    tools: list[ToolSchema] | None = None,
    reasoning_effort: ReasoningEffort | None = None,
    stream: bool = True,
) -> InteractStreamResponse | list[Content]
```

**Example:**

```python
import otto.lib as otto

# Quick streaming query
stream = otto.quick_query(
    "Explain quantum computing in simple terms",
    model="anthropic/claude-3-5-sonnet-20241022",
    stream=True
)
for chunk in stream:
    print(chunk.get("content", ""), end="")

# Quick non-streaming query
response = otto.quick_query(
    "What is the capital of France?",
    instruction="You are a geography expert",
    stream=False
)
for content in response:
    if content["type"] == "text":
        print(content["text"])
```
