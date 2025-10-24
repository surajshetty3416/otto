import contextlib
from typing import cast
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

import otto.lib.model as model
from otto.lib.tests.utils import delete_sessions, print_stats
from otto.lib.types import Provider
from otto.llm.test_llm.utils import skip_unless_can_run_llm_tests


def mock_get_key(provider: Provider) -> tuple[str | None, str | None]:
	"""Mock get_key so that tests don't fail if API keys are not set."""
	provider_keys = {
		"OpenAI": ("OPENAI_API_KEY", "mock-openai-key"),
		"Anthropic": ("ANTHROPIC_API_KEY", "mock-anthropic-key"),
		"Google": ("GEMINI_API_KEY", "mock-gemini-key"),
	}
	return provider_keys.get(provider, (None, None))


@patch("otto.llm.utils.get_key", side_effect=mock_get_key)
class TestModelAvailability(UnitTestCase):
	"""Test model and provider availability checks."""

	def test_is_model_available_exact_match(self, mock_get_key):
		"""Test exact model name matching from fixtures."""
		# Test with models that exist in fixtures
		self.assertTrue(model.is_model_available("anthropic/claude-3-5-haiku-latest"))
		self.assertTrue(model.is_model_available("openai/gpt-4o"))
		self.assertTrue(model.is_model_available("gemini/gemini-2.5-flash"))

		# Test with models that don't exist
		self.assertFalse(model.is_model_available("nonexistent/model"))
		self.assertFalse(model.is_model_available(""))

	def test_is_model_available_partial_match(self, mock_get_key):
		"""Test partial model name matching."""
		# Test partial matching with exact=False
		self.assertTrue(model.is_model_available("claude", exact=False))
		self.assertTrue(model.is_model_available("gpt", exact=False))
		self.assertTrue(model.is_model_available("gemini", exact=False))

		# Test case insensitive matching
		self.assertTrue(model.is_model_available("CLAUDE", exact=False))
		self.assertTrue(model.is_model_available("GPT", exact=False))

		# Test non-existent partial matches
		self.assertFalse(model.is_model_available("nonexistent", exact=False))

	def test_is_model_available_disabled_models(self, mock_get_key):
		"""Test that disabled models return False."""
		# openai/o3 is disabled in fixtures (enabled: 0)
		self.assertFalse(model.is_model_available("openai/o3"))

	def test_is_provider_available_with_key(self, mock_get_key):
		"""Test provider availability when API key is set."""
		self.assertTrue(model.is_provider_available("OpenAI"))
		self.assertTrue(model.is_provider_available("Anthropic"))
		self.assertTrue(model.is_provider_available("Google"))


@patch("otto.llm.utils.get_key", side_effect=mock_get_key)
class TestModelRetrieval(UnitTestCase):
	"""Test model filtering and retrieval functions."""

	def test_get_models_basic_filtering(self, mock_get_key):
		"""Test basic model filtering by various criteria."""

		# Test filtering by provider
		anthropic_models = model.get_models(provider="Anthropic")
		self.assertGreater(len(anthropic_models), 0)
		for m in anthropic_models:
			self.assertTrue(m.startswith("anthropic/"))

		# Test filtering by size
		small_models = model.get_models(size="Small")
		self.assertGreater(len(small_models), 0)

		# Test filtering by reasoning capability
		reasoning_models = model.get_models(is_reasoning=True)
		self.assertGreater(len(reasoning_models), 0)

		# Test filtering by image support
		image_models = model.get_models(supports_vision=True)
		self.assertGreater(len(image_models), 0)

	def test_get_models_combined_filters(self, mock_get_key):
		"""Test combining multiple filter criteria."""
		# Test multiple filters
		filtered_models = model.get_models(
			provider="Anthropic", size="Medium", is_reasoning=True, supports_vision=True
		)
		self.assertGreater(len(filtered_models), 0)
		for m in filtered_models:
			self.assertTrue(m.startswith("anthropic/"))

	def test_get_model_with_preference(self, mock_get_key):
		"""Test model selection with preference."""

		# Test with preference that exists
		preferred_model = model.get_model(preference="claude")
		self.assertIsNotNone(preferred_model)
		if preferred_model:
			self.assertIn("claude", preferred_model.lower())

		# Test with preference that doesn't exist but fallback available
		fallback_model = model.get_model(provider="OpenAI", preference="nonexistent-model")
		self.assertIsNotNone(fallback_model)
		if fallback_model:
			self.assertTrue(fallback_model.startswith("openai/"))

	def test_get_models_with_details_flag(self, mock_get_key):
		"""Test get_models returns details when get_details=True."""

		# Test without get_details (default behavior - should return list of strings)
		models_without_details = model.get_models(provider="Anthropic")
		self.assertGreater(len(models_without_details), 0)
		self.assertIsInstance(models_without_details[0], str)

		# Test with get_details=False (explicit - should return list of strings)
		models_explicit_false = model.get_models(provider="Anthropic", get_details=False)
		self.assertGreater(len(models_explicit_false), 0)
		self.assertIsInstance(models_explicit_false[0], str)

		# Test with get_details=True (should return list of ModelDetails)
		models_with_details = model.get_models(provider="Anthropic", get_details=True)
		self.assertGreater(len(models_with_details), 0)
		self.assertIsInstance(models_with_details[0], dict)

		# Verify ModelDetails structure
		model_detail = models_with_details[0]
		self.assertIn("name", model_detail)
		self.assertIn("title", model_detail)
		self.assertIn("provider", model_detail)
		self.assertIn("size", model_detail)
		self.assertIn("is_reasoning", model_detail)
		self.assertIn("supports_vision", model_detail)
		self.assertIn("is_enabled", model_detail)
		self.assertIn("is_api_key_set", model_detail)

		# Verify provider matches
		self.assertEqual(model_detail["provider"], "Anthropic")

	def test_get_model_with_details_flag(self, mock_get_key):
		"""Test get_model returns details when get_details=True."""

		# Test without get_details (default behavior - should return string)
		model_without_details = model.get_model(provider="OpenAI")
		self.assertIsNotNone(model_without_details)
		self.assertIsInstance(model_without_details, str)

		# Test with get_details=False (explicit - should return string)
		model_explicit_false = model.get_model(provider="OpenAI", get_details=False)
		self.assertIsNotNone(model_explicit_false)
		self.assertIsInstance(model_explicit_false, str)

		# Test with get_details=True (should return ModelDetails)
		model_with_details = model.get_model(provider="OpenAI", get_details=True)
		self.assertIsNotNone(model_with_details)
		self.assertIsInstance(model_with_details, dict)

		assert model_with_details is not None

		# Verify ModelDetails structure
		self.assertIn("name", model_with_details)
		self.assertIn("title", model_with_details)
		self.assertIn("provider", model_with_details)
		self.assertIn("size", model_with_details)
		self.assertIn("is_reasoning", model_with_details)
		self.assertIn("supports_vision", model_with_details)
		self.assertIn("is_enabled", model_with_details)
		self.assertIn("is_api_key_set", model_with_details)

		# Verify provider matches
		self.assertEqual(model_with_details["provider"], "OpenAI")

	def test_get_model_with_preference_and_details(self, mock_get_key):
		"""Test get_model with both preference and get_details flags."""

		# Test preference with get_details=True
		model_with_preference_and_details = model.get_model(preference="claude", get_details=True)
		self.assertIsNotNone(model_with_preference_and_details)
		self.assertIsInstance(model_with_preference_and_details, dict)

		assert model_with_preference_and_details is not None

		# Verify the preference was applied
		self.assertIn("claude", model_with_preference_and_details["name"].lower())

		# Verify ModelDetails structure
		self.assertIn("name", model_with_preference_and_details)
		self.assertIn("title", model_with_preference_and_details)
		self.assertIn("provider", model_with_preference_and_details)


class TestAPIKeyManagement(UnitTestCase):
	"""Test API key setting functionality."""

	@patch("frappe.set_value")
	def test_set_api_key_valid_provider(self, mock_set_value):
		"""Test setting API key for valid provider."""
		model.set_api_key("OpenAI", "test-key-value")
		mock_set_value.assert_called_once_with(
			"Otto Settings", "Otto Settings", "openai_api_key", "test-key-value"
		)

	@patch("frappe.set_value")
	def test_set_api_key_invalid_provider(self, mock_set_value):
		"""Test setting API key for invalid provider."""

		model.set_api_key(cast("Provider", "InvalidProvider"), "test-key-value")
		mock_set_value.assert_not_called()


class TestModelCreationAndUsage(UnitTestCase):
	"""Test model creation and actual usage with LLM integration."""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.created_models = []
		self.created_sessions = []

	def setUp(self):
		"""Set up test fixtures."""
		self.created_models = []
		self.created_sessions = []

	def delete_model_if_exists(self, model_name: str) -> None:
		"""Delete a model if it exists, suppressing any errors."""
		try:
			if frappe.db.exists("Otto LLM", model_name):
				frappe.delete_doc("Otto LLM", model_name, force=True)
				frappe.db.commit()
		except Exception:
			# Suppress any errors during deletion
			pass

	def tearDown(self):
		"""Clean up created test artifacts."""
		print_stats(self.created_sessions)
		delete_sessions(self.created_sessions)

		for model_name in self.created_models:
			with contextlib.suppress(Exception):
				frappe.delete_doc("Otto LLM", model_name, force=True)

		frappe.db.commit()

	@skip_unless_can_run_llm_tests
	def test_create_model_and_use_for_task(self):
		"""Test creating a model and using it for a simple LLM task."""
		# Delete model if it exists before creating
		test_model_name = "openai/gpt-4.1-nano-2025-04-14"
		self.delete_model_if_exists(test_model_name)

		# Create a test model
		model_name = model.create_model(
			title="Test GPT-4.1-nano Model",
			provider="OpenAI",
			provider_model_id="gpt-4.1-nano-2025-04-14",
			size="Very Small",
			is_reasoning=False,
			supports_vision=True,
		)
		self.created_models.append(model_name)
		self.assertTrue(model.is_model_available(model_name))

		available_models = model.get_models(provider="OpenAI", size="Very Small")
		self.assertIn(model_name, available_models)

		# Use the created model for a simple task
		import otto.lib as lib

		test_session = lib.new(
			model=model_name, instruction="You are a helpful assistant. Respond concisely."
		)
		self.created_sessions.append(test_session)

		# Perform a simple interaction
		response, error = test_session.interact("Say hello!", stream=False)

		# Verify the interaction worked
		self.assertIsNone(error, f"LLM interaction failed: {error}")
		self.assertIsNotNone(response)
		if response:
			self.assertIsInstance(response, dict)
			self.assertIn("content", response)
			self.assertGreater(len(response["content"]), 0)

			# Verify response contains text
			has_text_content = any(
				content.get("type") == "text" and content.get("text", "").strip()
				for content in response["content"]
			)
			self.assertTrue(has_text_content, "Response should contain text content")

	def test_create_model_name_format(self):
		"""Test that created model names follow expected format."""
		# Delete models if they exist before creating
		openai_model_name = "openai/gpt-4o-test"
		anthropic_model_name = "anthropic/claude-test"
		google_model_name = "gemini/gemini-test"

		self.delete_model_if_exists(openai_model_name)
		self.delete_model_if_exists(anthropic_model_name)
		self.delete_model_if_exists(google_model_name)

		# Test OpenAI model
		openai_model = model.create_model(
			title="Test OpenAI Model",
			provider="OpenAI",
			provider_model_id="gpt-4o-test",
			size="Medium",
			is_reasoning=False,
			supports_vision=True,
		)
		self.created_models.append(openai_model)
		self.assertEqual(openai_model, "openai/gpt-4o-test")

		# Test Anthropic model
		anthropic_model = model.create_model(
			title="Test Anthropic Model",
			provider="Anthropic",
			provider_model_id="claude-test",
			size="Large",
			is_reasoning=True,
			supports_vision=True,
		)
		self.created_models.append(anthropic_model)
		self.assertEqual(anthropic_model, "anthropic/claude-test")

		# Test Google model (should use 'gemini' as provider_id)
		google_model = model.create_model(
			title="Test Google Model",
			provider="Google",
			provider_model_id="gemini-test",
			size="Small",
			is_reasoning=True,
			supports_vision=False,
		)
		self.created_models.append(google_model)
		self.assertEqual(google_model, "gemini/gemini-test")

	def test_create_model_properties(self):
		"""Test that created model has correct properties."""
		# Delete model if it exists before creating
		test_model_name = "openai/test-model-props"
		self.delete_model_if_exists(test_model_name)

		model_name = model.create_model(
			title="Test Model Properties",
			provider="OpenAI",
			provider_model_id="test-model-props",
			size="Medium",
			is_reasoning=True,
			supports_vision=False,
		)
		self.created_models.append(model_name)

		# Verify model exists and has correct properties
		model_doc = frappe.get_doc("Otto LLM", model_name)
		self.assertEqual(model_doc.get("title"), "Test Model Properties")
		self.assertEqual(model_doc.get("provider"), "OpenAI")
		self.assertEqual(model_doc.get("size"), "Medium")
		self.assertTrue(model_doc.get("is_reasoning"))
		self.assertFalse(model_doc.get("supports_vision"))
		self.assertTrue(model_doc.get("enabled"))  # Should be enabled by default
