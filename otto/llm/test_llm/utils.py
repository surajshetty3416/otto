import os
import unittest
from collections.abc import Callable
from inspect import isclass
from textwrap import dedent

import click
import frappe

from otto.llm.utils import get_key

# Model to use for testing
TEST_MODEL = "openai/gpt-4.1-mini"  # current cheapest model

get_weather_tool = {
	"type": "function",
	"function": {
		"name": "get_weather",
		"description": "Get the current weather in a given location",
		"parameters": {
			"type": "object",
			"properties": {
				"location": {
					"type": "string",
					"description": "The city and state, e.g. San Francisco, CA",
				},
				"unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
			},
			"required": ["location"],
		},
	},
}


def can_run_llm_tests():
	"""
	Check if LLM tests can be run.

	LLM tests are disabled by default, set RUN_LLM_TESTS=true to enable.
	"""
	if os.environ.get("RUN_LLM_TESTS", "false").lower() != "true":
		return False

	assert TEST_MODEL.startswith("openai/"), "update provider check in the next line"
	key, value = get_key("OpenAI")
	if key is None or value is None:
		click.secho(
			"LLM tests enabled but API keys for OpenAI are needed to run. Set OPENAI_API_KEY as an envvar or in Otto Settings.",
			fg="red",
		)
		return False

	return True


def get_testfile_path(file_name: str):
	return os.path.join(
		frappe.get_app_path("otto"),
		"llm",
		"test_llm",
		file_name,
	)


def skip_unless_can_run_llm_tests(test_case: type[unittest.TestCase] | Callable):
	"""
	Skip a test if LLM tests cannot be run.
	"""

	reason = dedent("""
	LLM integration tests are disabled, these tests require API keys to be set
	and so cost money to run. Set RUN_LLM_TESTS=true to enable.
	""")

	if isclass(test_case):
		return unittest.skipUnless(can_run_llm_tests(), reason=reason)(test_case)

	if can_run_llm_tests():
		return test_case

	return unittest.skip(reason=reason)(test_case)
