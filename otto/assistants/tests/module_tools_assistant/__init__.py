"""Test assistant that uses module objects to specify tools."""

from otto.assistants.test import simple_tool

uid = "test-module-tools-assistant"
name = "Module Tools Test Assistant"
dev_mode_only = False

instruction = "Test assistant using module objects for tools."

# Tools specified as module objects
tools = [simple_tool]
