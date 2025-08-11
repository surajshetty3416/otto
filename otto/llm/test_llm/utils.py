import os
import unittest
from collections.abc import Callable
from inspect import isclass
from textwrap import dedent

import click
import frappe

from otto.llm.types import SessionStats
from otto.llm.utils import get_key

# Model to use for testing
TEST_MODEL = "openai/gpt-5-nano"  # current cheapest model

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


def print_stats(statss: list[SessionStats | None]):
	total_cost = 0
	total_llm_calls = 0
	total_input_tokens = 0
	total_output_tokens = 0
	total_duration = 0
	latencies = []
	ttfc = []

	skip = True

	for ss in statss:
		if not ss:
			continue
		skip = False

		cost_val = ss.get("cost", 0)
		llm_calls_val = ss.get("llm_calls", 0)
		input_tokens_val = ss.get("total_input_tokens", 0)
		output_tokens_val = ss.get("total_output_tokens", 0)
		duration_val = ss.get("duration", 0)

		cost = float(cost_val) if isinstance(cost_val, int | float) else 0.0
		llm_calls = int(llm_calls_val) if isinstance(llm_calls_val, int | float) else 0
		input_tokens = int(input_tokens_val) if isinstance(input_tokens_val, int | float) else 0
		output_tokens = int(output_tokens_val) if isinstance(output_tokens_val, int | float) else 0
		duration = float(duration_val) if isinstance(duration_val, int | float) else 0.0

		# Add to totals
		total_cost += cost
		total_llm_calls += llm_calls
		total_input_tokens += input_tokens
		total_output_tokens += output_tokens
		total_duration += duration
		latencies.append(ss["inter_chunk_latency"])
		ttfc.append(ss["time_to_first_chunk"])

	if skip:
		return

	print(f"Calls: {total_llm_calls}", end="\t")
	print(f"Cost: ${total_cost:.6f}", end="\t")
	print(f"Input: {total_input_tokens}tok", end="\t")
	print(f"Output: {total_output_tokens}tok", end="\t")
	print(f"Latency: {(sum(latencies) / (len(latencies) or 1) * 1000):.3f}ms", end="\t")
	print(f"TTFC: {sum(ttfc) / (len(ttfc) or 1):.3f}s", end="\t")
	print(f"Duration: {total_duration:.3f}s")
