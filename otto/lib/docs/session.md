# Session

High-level LLM interaction state management.

## Exports

- `Session`: Class for managing LLM interaction state.
- `new`: Create a new session.
- `load`: Load a session from a DocType.
- `quick_query`: A convenience function for one-off LLM queries without session management.

## Example

```python
import otto.lib as otto

# Create new session
session = otto.new(
    model="anthropic/claude-3-5-sonnet-20241022",
    instruction="You are a helpful coding assistant",
    tools=[calculator_tool_schema],
)

# Interact with streaming
stream = session.interact("Calculate 15 * 23", stream=True)
for chunk in stream:
    print(chunk.get("text", ""), end="")
result = stream.item

# Handle tool use
pending_tools = session.get_pending_tool_use()
for tool in pending_tools:
    result = execute_tool(tool.name, tool.args)
    session.update_tool_use(ToolUseUpdate(id=tool.id, status="success", result=result))

# Continue conversation
response, _ = session.interact("What was the result?", stream=False)
if response:
    print(response["content"])
```

## Tool Use
