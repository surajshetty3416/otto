"""Test assistant that uses string paths to specify tools."""

uid = "test-string-tools-assistant"
name = "String Tools Test Assistant"
dev_mode_only = False

instruction = "Test assistant using string paths for tools."

# Tools specified as string paths to modules
tools = ["otto.assistants.test.simple_tool"]
