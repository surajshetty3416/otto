from typing import cast

from frappe.tests import UnitTestCase

from otto.lib.session import Session, quick_query
from otto.lib.tests.utils import delete_sessions, print_stats
from otto.llm.test_llm.utils import (
	TEST_MODEL,
	get_testfile_path,
	get_weather_tool,
	skip_unless_can_run_llm_tests,
)
from otto.llm.types import ToolSchema, ToolUseUpdate
from otto.llm.utils import to_content

# Convert get_weather_tool to ToolSchema format
weather_tool_schema: ToolSchema = cast("ToolSchema", get_weather_tool["function"])

TEST_INSTRUCTION = (
	"You are a helpful assistant. Be as concise as possible and respond only with what's needed."
)


class TestSessions(UnitTestCase):
	"""
	Tests for the Session library wrapper around OttoSession.

	Tests marked with @skip_unless_can_run_llm_tests require:
	- Network connectivity to the LLM provider
	- Environment variable RUN_LLM_TESTS=true to be set
	- Valid API keys for the LLM provider
	"""

	def setUp(self):
		"""Set up test fixtures."""
		self.created_sessions: list[Session] = []

	def tearDown(self):
		"""Clean up created test artifacts and print API usage stats."""
		print_stats(self.created_sessions)
		delete_sessions(self.created_sessions)

	def test_session_creation(self):
		"""Test basic session creation and properties."""
		session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
		)
		self.created_sessions.append(session)

		self.assertIsInstance(session.id, str)
		self.assertEqual(session.model, TEST_MODEL)
		self.assertEqual(session.instruction, TEST_INSTRUCTION)
		self.assertFalse(session.is_active)
		self.assertIsNone(session.failure_reason)
		self.assertEqual(session.get_llm_call_count(), 0)
		self.assertEqual(len(session.get_items()), 0)
		self.assertIsNone(session.get_last_item())
		self.assertIsNone(session.get_last_response())

	def test_session_load(self):
		"""Test loading an existing session."""
		# Create a session first
		original_session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
		)
		self.created_sessions.append(original_session)
		session_id = original_session.id

		# Load the session
		loaded_session = Session.load(session_id)

		self.assertEqual(loaded_session.id, session_id)
		self.assertEqual(loaded_session.model, TEST_MODEL)
		self.assertEqual(loaded_session.instruction, TEST_INSTRUCTION)

	@skip_unless_can_run_llm_tests
	def test_basic_interaction(self):
		"""Test basic interaction without tools."""
		session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
		)
		self.created_sessions.append(session)

		# Test streaming interaction
		stream_response = session.interact("Hello! Please respond with just 'Hi!'", stream=True)
		chunks = []
		for chunk in stream_response:
			chunks.append(chunk)

		# Check stream response properties
		self.assertIsNotNone(stream_response.item)
		self.assertIsInstance(stream_response.content, list)
		self.assertIsNone(stream_response.failure_reason)
		self.assertGreater(len(chunks), 0)

		# Verify chunks match item content
		chunks_text = "".join(c["content"] for c in chunks if c["type"] in ["text", "thinking"])
		item_text = "".join(
			c["text"] for c in stream_response.content if c["type"] == "text" or c["type"] == "thinking"
		)
		self.assertEqual(chunks_text, item_text)

		# Check session state after interaction
		self.assertEqual(session.get_llm_call_count(), 1)
		self.assertEqual(len(session.get_items()), 2)  # User query + Agent response

		last_item = session.get_last_item()
		self.assertIsNotNone(last_item)
		assert last_item is not None, "type check"
		self.assertEqual(last_item["meta"]["role"], "agent")
		self.assertEqual(last_item, stream_response.item)

		last_response = session.get_last_response()
		self.assertIsNotNone(last_response)
		self.assertIsInstance(last_response, list)

	@skip_unless_can_run_llm_tests
	def test_non_streaming_interaction(self):
		"""Test non-streaming interaction."""
		session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
		)
		self.created_sessions.append(session)

		# Test non-streaming interaction
		response, reason = session.interact("Hello!", stream=False)

		self.assertIsNone(reason)
		self.assertIsNotNone(response)
		assert response is not None  # for type checker
		self.assertEqual(response["meta"]["role"], "agent")
		self.assertIsInstance(response["content"], list)

	@skip_unless_can_run_llm_tests
	def test_tool_call_workflow(self):
		"""Test complete tool calling workflow."""
		session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
			tools=[weather_tool_schema],
		)
		self.created_sessions.append(session)

		# Step 1: Ask for weather, expect tool use
		stream_response = session.interact("What is the weather like in London?", stream=True)
		chunks = list(stream_response)  # Consume the stream

		self.assertIsNotNone(stream_response.item)
		self.assertIsNone(stream_response.failure_reason)
		self.assertGreater(len(chunks), 0)

		# Check that tool use was requested
		pending_tools = session.get_pending_tool_use()
		self.assertGreater(len(pending_tools), 0, "Expected at least one pending tool use")

		weather_tool = pending_tools[0]
		self.assertEqual(weather_tool.name, "get_weather")
		self.assertIn("london", weather_tool.args["location"].lower())

		# Check session state
		last_response = session.get_last_response()
		self.assertIsNotNone(last_response)
		assert last_response is not None, "type check"

		# Verify tool use content in response
		has_tool_use = False
		for content in last_response:
			if content["type"] == "tool_use":
				has_tool_use = True
				self.assertEqual(content["name"], "get_weather")
				self.assertEqual(content["status"], "pending")
				break

		self.assertTrue(has_tool_use, "Expected tool_use content in agent response")

		# Step 2: Update tool use with result
		tool_update = ToolUseUpdate(
			id=weather_tool.id, result="The weather in London is 15°C and partly cloudy."
		)
		session.update_tool_use(tool_update)

		# Verify tool use status updated
		updated_response = session.get_last_response()
		self.assertIsNotNone(updated_response)
		assert updated_response is not None, "type check"

		for content in updated_response:
			if content["type"] == "tool_use" and content["id"] == weather_tool.id:
				self.assertEqual(content["status"], "success")
				self.assertEqual(content["result"], "The weather in London is 15°C and partly cloudy.")
				break
		else:
			self.fail("Tool use content not found or not updated properly")

		# Step 3: Continue conversation, expect LLM to use tool result
		final_response = session.interact(stream=True)
		final_chunks = list(final_response)

		self.assertIsNotNone(final_response.item)
		self.assertIsNone(final_response.failure_reason)
		self.assertGreater(len(final_chunks), 0)

		# Check that no new tools are pending
		new_pending_tools = session.get_pending_tool_use()
		self.assertEqual(len(new_pending_tools), 0, "No new tools should be pending")

		# Verify the response mentions the weather information
		final_text = ""
		for content in final_response.content:
			if content["type"] == "text" or content["type"] == "thinking":
				final_text += content["text"]

		self.assertTrue(
			any(term in final_text.lower() for term in ["15", "london", "cloudy", "weather"]),
			f"Expected weather information in final response: {final_text}",
		)

	@skip_unless_can_run_llm_tests
	def test_multiple_tool_calls(self):
		"""Test handling multiple tool calls in one response."""
		session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
			tools=[weather_tool_schema],
		)
		self.created_sessions.append(session)

		# Ask for weather in multiple cities
		response = session.interact("What is the weather like in London and Paris?", stream=True)
		list(response)  # Consume stream

		# Get all pending tool uses
		pending_tools = session.get_pending_tool_use()
		self.assertGreaterEqual(len(pending_tools), 1, "Expected at least one tool call")

		# Update all tool uses
		updates = []
		for tool in pending_tools:
			city = "London" if "london" in tool.args["location"].lower() else "Paris"
			temp = "15°C" if city == "London" else "18°C"
			updates.append(ToolUseUpdate(id=tool.id, result=f"The weather in {city} is {temp} and sunny."))

		session.update_tool_use(updates)

		# Verify all tools are updated
		last_response = session.get_last_response()
		self.assertIsNotNone(last_response)
		assert last_response is not None  # for type checker

		updated_tools = [c for c in last_response if c["type"] == "tool_use"]
		for tool_content in updated_tools:
			self.assertEqual(tool_content["status"], "success")
			self.assertIsNotNone(tool_content["result"])

	@skip_unless_can_run_llm_tests
	def test_image_recognition(self):
		"""Test image recognition capabilities."""
		image_file = get_testfile_path("test.png")
		query = to_content(["What do you see in this image?", image_file])

		session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
		)
		self.created_sessions.append(session)

		response = session.interact(query, stream=True)
		chunks = list(response)  # Consume stream

		self.assertIsNotNone(response.item)
		self.assertIsNone(response.failure_reason)
		self.assertGreater(len(chunks), 0)

		# Extract text from response
		response_text = ""
		for content in response.content:
			if content["type"] == "text" or content["type"] == "thinking":
				response_text += content["text"]

		# The test image should contain "Test" based on test_litellm.py
		self.assertIn(
			"test", response_text.lower(), f"Expected 'Test' in image recognition response: {response_text}"
		)

		# Verify session state
		self.assertEqual(session.get_llm_call_count(), 1)
		self.assertEqual(len(session.get_items()), 2)

	@skip_unless_can_run_llm_tests
	def test_document_recognition(self):
		"""Test document recognition capabilities."""
		pdf_file = get_testfile_path("test.pdf")
		query = to_content(["What is the content of this document?", pdf_file])

		session = Session.new(
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
		)
		self.created_sessions.append(session)

		response = session.interact(query, stream=True)
		chunks = list(response)  # Consume stream

		self.assertIsNotNone(response.item)
		self.assertIsNone(response.failure_reason)
		self.assertGreater(len(chunks), 0)

		# Extract text from response
		response_text = ""
		for content in response.content:
			if content["type"] in ["text", "thinking"]:
				assert content["type"] == "text" or content["type"] == "thinking", "type check"
				response_text += content["text"]

		# The test PDF should contain "Test" based on test_litellm.py
		self.assertIn(
			"test",
			response_text.lower(),
			f"Expected 'test' in document recognition response: {response_text}",
		)

		# Verify session state
		self.assertEqual(session.get_llm_call_count(), 1)
		self.assertEqual(len(session.get_items()), 2)

	@skip_unless_can_run_llm_tests
	def test_quick_query_streaming(self):
		"""Test quick_query function with streaming."""
		response = quick_query(
			"Hello! Please respond briefly.",
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
			stream=True,
		)

		chunks = list(response)  # Consume stream

		self.assertIsNotNone(response.item)
		self.assertIsInstance(response.content, list)
		self.assertIsNone(response.failure_reason)
		self.assertGreater(len(chunks), 0)

	@skip_unless_can_run_llm_tests
	def test_quick_query_non_streaming(self):
		"""Test quick_query function without streaming."""
		content = quick_query(
			"Hello! Please respond briefly.",
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
			stream=False,
		)

		self.assertIsInstance(content, list)
		self.assertGreater(len(content), 0)

		# Check content structure
		first_content = content[0]
		self.assertIn(first_content["type"], ["text", "thinking"])
		if first_content["type"] == "text":
			self.assertIsInstance(first_content["text"], str)
			self.assertGreater(len(first_content["text"]), 0)

	@skip_unless_can_run_llm_tests
	def test_quick_query_with_tools(self):
		"""Test quick_query function with tools."""
		response = quick_query(
			"What is the weather like in Tokyo?",
			model=TEST_MODEL,
			instruction=TEST_INSTRUCTION,
			tools=[weather_tool_schema],
			stream=True,
		)

		chunks = list(response)  # Consume stream

		self.assertIsNotNone(response.item)
		self.assertIsInstance(response.content, list)
		self.assertGreater(len(chunks), 0)

		# Check for tool use in content
		has_tool_use = any(c["type"] == "tool_use" for c in response.content)
		self.assertTrue(has_tool_use, "Expected tool use in quick_query response")

		# Check that the weather tool was called
		tool_calls = [c for c in response.content if c["type"] == "tool_use"]
		self.assertEqual(tool_calls[0]["name"], "get_weather", "Expected weather tool to be called")

	def test_get_pending_tool_use_empty(self):
		"""Test get_pending_tool_use when no tools are pending."""
		session = Session.new(model=TEST_MODEL)
		self.created_sessions.append(session)

		# No interactions yet
		pending = session.get_pending_tool_use()
		self.assertEqual(len(pending), 0)

		# Test with last_item_only=False
		pending_all = session.get_pending_tool_use(last_item_only=False)
		self.assertEqual(len(pending_all), 0)

	def test_reasoning_effort_property(self):
		"""Test reasoning_effort property handling."""
		# Test with no reasoning effort
		session = Session.new(model=TEST_MODEL)
		self.created_sessions.append(session)
		self.assertEqual(session.reasoning_effort, "None")

		# Test with valid reasoning effort
		session_with_effort = Session.new(
			model=TEST_MODEL,
			reasoning_effort="Medium",
		)
		self.created_sessions.append(session_with_effort)
		self.assertEqual(session_with_effort.reasoning_effort, "Medium")
