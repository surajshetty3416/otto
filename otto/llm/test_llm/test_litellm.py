import unittest

from otto.llm.litellm import interact
from otto.llm.test_llm.utils import (
	TEST_MODEL,
	get_testfile_path,
	get_weather_tool,
	print_stats,
	skip_unless_can_run_llm_tests,
)
from otto.llm.types import ToolUseUpdate
from otto.llm.utils import get_stats, to_content, update_tool_use
from otto.utils import drain


#  Skip if not explicitly enabled
@skip_unless_can_run_llm_tests
class TestLiteLLMIntegration(unittest.TestCase):
	"""
	Integration tests for the litellm interact function using {TEST_MODEL_NAME}.

	Requires:
	- Network connectivity to the LLM provider.
	- Environment variable RUN_LLM_TESTS=true to be set.
	"""

	def test_basic_interaction(self):
		"""Test simple question answering."""
		query = "Hello!"
		system_prompt = "You are a concise assistant."

		# Use the specific test model
		response, error = drain(interact(query, system=system_prompt, model=TEST_MODEL))

		# Basic checks
		self.assertIsNone(error, f"Interaction failed with error: {error}")
		self.assertIsNotNone(response)
		assert response is not None  # for type checker

		# Check response structure
		self.assertIsInstance(response, dict)  # InteractReturn is a TypedDict
		self.assertIsInstance(response["item"], dict)  # SessionItem is a TypedDict
		self.assertIsInstance(response["update"], dict)  # Session is a TypedDict
		self.assertIsInstance(response["chunks"], list)

		# Check agent item
		agent_item = response["item"]
		self.assertEqual(agent_item["meta"]["role"], "agent")
		self.assertIsInstance(agent_item["content"], list)
		self.assertGreater(len(agent_item["content"]), 0, "Agent response content is empty")

		# Check the type of the first content block (usually text for simple Q&A)
		first_content = agent_item["content"][0]

		# Allow thinking, text or tool_use (though unlikely for this query)
		self.assertIn(first_content["type"], ["text", "thinking", "tool_use"])
		text = ""
		if first_content["type"] == "text":
			self.assertEqual(first_content["type"], "text")
			self.assertIsInstance(first_content["text"], str)
			self.assertGreater(len(first_content["text"]), 0)
			text = first_content["text"]
		elif first_content["type"] == "thinking":
			self.assertEqual(first_content["type"], "thinking")
			self.assertIsInstance(first_content["text"], str)
			self.assertGreater(len(first_content["text"]), 0)
			text = first_content["text"]

		# Check update structure (basic)
		# Ensure update is not None before accessing items
		self.assertIsNotNone(response["update"])
		assert response["update"] is not None  # for type checker

		session = response["update"]
		print_stats([get_stats(session)])

		self.assertIsInstance(session["items"], dict)
		self.assertEqual(len(session["items"]), 2)  # User query + Agent response

		first_key = session["first"]
		second_key = session["items"][first_key]["next"][0]
		first_item = session["items"][first_key]
		second_item = session["items"][second_key]

		self.assertEqual(first_item["meta"]["role"], "user")
		self.assertEqual(second_item["meta"]["role"], "agent")
		self.assertEqual(second_item["id"], agent_item["id"])

		# Check if the correct model name is reported
		self.assertEqual(agent_item["meta"]["model"], TEST_MODEL)
		self.assertIn("input_tokens", agent_item["meta"])
		self.assertIn("output_tokens", agent_item["meta"])
		self.assertIn("cost", agent_item["meta"])
		self.assertIn("end_reason", agent_item["meta"])

		# For a simple response, end_reason should ideally be 'turn_end' or 'stop'
		self.assertEqual(agent_item["meta"]["end_reason"], "turn_end")

		# Check chunks
		self.assertGreater(len(response["chunks"]), 0, "No stream chunks received")
		first_chunk = response["chunks"][0]
		self.assertIn("type", first_chunk)
		self.assertIn("content", first_chunk)
		self.assertIn("item_id", first_chunk)
		self.assertEqual(first_chunk["item_id"], agent_item["id"])
		self.assertTrue(first_chunk["content"] in text)

	def test_tool_calling(self):
		"""Test interaction involving a tool call."""
		query = "What is the weather like in London?"
		tools = [get_weather_tool]

		# Use the specific test model known for tool calling
		response, error = drain(interact(query, tools=tools, model=TEST_MODEL))

		self.assertIsNone(error, f"Interaction failed with error: {error}")
		self.assertIsNotNone(response)
		assert response is not None  # for type checker
		session = response["update"]
		print_stats([get_stats(session)])

		# Check response structure (similar to basic test)
		self.assertIsInstance(response, dict)
		self.assertIn("item", response)
		agent_item = response["item"]
		self.assertIn("update", response)
		self.assertIn("chunks", response)

		# Check agent item content for ToolUseContent
		self.assertEqual(agent_item["meta"]["role"], "agent")
		self.assertIsInstance(agent_item["content"], list)
		self.assertGreater(len(agent_item["content"]), 0, "Agent response content is empty")

		has_tool_use = False
		for content in agent_item["content"]:
			if content["type"] != "tool_use":
				continue

			has_tool_use = True
			self.assertEqual(content["type"], "tool_use")
			self.assertIn("id", content)
			self.assertIn("name", content)
			self.assertIn("args", content)
			self.assertEqual(content["name"], "get_weather")
			self.assertTrue("london" in content["args"]["location"].lower())

		self.assertTrue(has_tool_use, "No tool use content found in agent response")

	def test_multiple_tool_calls(self):
		query = "What is the weather like in London and Paris?"
		tools = [get_weather_tool, get_weather_tool]
		response, error = drain(interact(query, tools=tools, model=TEST_MODEL))

		self.assertIsNone(error, f"Interaction failed with error: {error}")
		self.assertIsNotNone(response)
		assert response is not None  # for type checker
		agent_item = response["item"]

		session = response["update"]
		tool_use = [c for c in agent_item["content"] if c["type"] == "tool_use"]
		self.assertEqual(len(tool_use), 2)

		assert len(tool_use) == 2, "Expected 2 tool calls"
		update_tool_use(
			session=session,
			update=ToolUseUpdate(id=tool_use[0]["id"], result="10 degrees celsius"),
		)
		update_tool_use(
			session=session,
			update=ToolUseUpdate(id=tool_use[1]["id"], result="10 degrees celsius"),
		)

		response, error = drain(interact(session=session, model=TEST_MODEL))
		self.assertIsNone(error, f"Interaction failed with error: {error}")
		self.assertIsNotNone(response)
		assert response is not None  # for type checker

		print_stats([get_stats(response["update"])])

	def test_file_handling(self):
		file = get_testfile_path("test.pdf")
		query = to_content(["What is in this file?", file])
		response, error = drain(interact(query, model=TEST_MODEL))

		self.assertIsNone(error, f"Interaction failed with error: {error}")
		self.assertIsNotNone(response)
		assert response is not None  # for type checker
		print_stats([get_stats(response["update"])])

		agent_item = response["item"]
		self.assertEqual(agent_item["meta"]["role"], "agent")

		agent_text = ""
		for content in agent_item["content"]:
			if content["type"] == "text" or content["type"] == "thinking":
				agent_text += content["text"]

		self.assertIn("Test", agent_text, "Expected 'Test' in response text for PDF")

	def test_image_handling(self):
		file = get_testfile_path("test.png")
		query = to_content(["What is in this image?", file])
		response, error = drain(interact(query, model=TEST_MODEL))

		self.assertIsNone(error, f"Interaction failed with error: {error}")
		self.assertIsNotNone(response)
		assert response is not None  # for type checker
		print_stats([get_stats(response["update"])])

		agent_item = response["item"]
		self.assertEqual(agent_item["meta"]["role"], "agent")

		agent_text = ""
		for content in agent_item["content"]:
			if content["type"] == "text" or content["type"] == "thinking":
				agent_text += content["text"]

		self.assertIn("Test", agent_text, "Expected 'Test' in response text for PNG")
