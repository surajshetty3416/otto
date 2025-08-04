from typing import Any

import frappe

from otto.lib.types import ModelSize, Provider
from otto.llm import utils
from otto.utils import cache

__all__ = [
	"is_model_available",
	"is_provider_available",
	"create_model",
	"get_model",
	"get_models",
	"set_api_key",
]


def set_api_key(provider: Provider, value: str) -> None:
	"""Sets the API key for a provider.

	Args:
		provider: The provider to set the key for
		key: The API key to set
	"""
	if (key := utils.get_provider_key(provider)) is None:
		return

	frappe.set_value("Otto Settings", "Otto Settings", key.lower(), value)


@cache(ttl=60)
def is_model_available(model: str, exact: bool = True) -> bool:
	"""Checks if a given model name is available in Otto LLM.

	This function checks if a model exists and is enabled in the Otto LLM system.
	The check can be done either with exact matching or partial name matching.

	Args:
		model: The name of the model to check
		exact: If True, only returns True on exact name match. If False, also
			checks for partial case-insensitive matches.

	Returns:
		True if the model exists and is enabled, False otherwise.
	"""
	if (
		frappe.db.exists({"doctype": "Otto LLM", "name": model, "enabled": True})
		and (provider := utils.get_provider(model))
		and is_provider_available(provider)
	):
		return True

	if exact or not model:
		return False

	for res in frappe.get_all("Otto LLM", filters={"enabled": True}, fields=["name", "title"]):
		assert isinstance(res.name, str) and isinstance(res.title, str), "sanity check"
		if (
			(model.lower() in res.name.lower() or model.lower() in res.title.lower())
			and (provider := utils.get_provider(res.name))
			and is_provider_available(provider)
		):
			return True

	return False


def is_provider_available(provider: Provider) -> bool:
	"""Returns `True` if the provider is available.

	Args:
		provider: The provider to check.

	Returns:
		`True` if models from the provider are available, `False` otherwise.
	"""
	key, value = utils.get_key(provider)
	return bool(key and value)


def create_model(
	*,
	title: str,
	provider: Provider,
	provider_model_id: str,
	size: ModelSize,
	is_reasoning: bool,
	supports_vision: bool,
) -> str:
	"""Creates a new Otto LLM entry with the specified parameters.

	`provider_model_id` is the model id used by the provider. For reference:
	- Anthropic: https://docs.anthropic.com/en/docs/about-claude/models/overview#model-names
		eg: "claude-sonnet-4-20250514", "claude-3-5-haiku-latest"
	- OpenAI: https://platform.openai.com/docs/models (check Snapshots section under a model's page)
		eg: "o1-preview", "gpt-4.1-nano-2025-04-14"
	- Gemini: https://ai.google.dev/gemini-api/docs/models#model-variations
		eg: "gemini-2.5-flash", "gemini-2.5-pro"

	Args:
		title: Display name/title for the model
		provider: The LLM provider (OpenAI, Anthropic, Google)
		provider_model_id: Provider-specific model identifier
		size: Model size category (Very Small, Small, Medium, Large)
		is_reasoning: Whether model supports reasoning capabilities
		supports_vision: Whether model supports image input

	Returns:
		Name of the created model in format "{provider_id}/{provider_model_id}"
		eg: "gemini/gemini-2.5-flash", "anthropic/claude-sonnet-4-20250514"
	"""
	from otto.otto.doctype.otto_llm.otto_llm import OttoLLM

	provider_id = provider.lower()
	if provider == "Google":
		provider_id = "gemini"

	name = f"{provider_id}/{provider_model_id}"
	llm = OttoLLM.new(
		name=name,
		title=title,
		provider=provider,
		is_reasoning=is_reasoning,
		size=size,
		supports_vision=supports_vision,
	)
	assert llm.name is not None, "sanity check"
	return llm.name


def get_model(
	*,
	provider: Provider | None = None,
	size: ModelSize | None = None,
	is_reasoning: bool | None = None,
	supports_vision: bool | None = None,
	preference: str | None = None,
) -> str | None:
	"""Returns the first available model matching the given criteria.

	`preference` can be used to specify a model name that is preferred, if
	available this will be returned else a model matching rest of the criteria
	will be returned.

	`preference` does a case insensitive substring search against the model name.
	to check if a specific model is available use `is_model_available`.

	`preference` value should be a provider model id substring, for reference:
	- Anthropic: https://docs.anthropic.com/en/docs/about-claude/models/overview#model-names
		eg: "claude-sonnet-4-20250514", "claude-3-5-haiku-latest"
	- OpenAI: https://platform.openai.com/docs/models (check Snapshots section under a model's page)
		eg: "o1-preview", "gpt-4.1-nano-2025-04-14"
	- Gemini: https://ai.google.dev/gemini-api/docs/models#model-variations
		eg: "gemini-2.5-flash", "gemini-2.5-pro"

	If a specific model is not available, use `create_model` to create it.

	Args:
		provider: Filter by specific provider (OpenAI, Anthropic, etc)
		size: Filter by model size (Very Small, Small, Medium, Large)
		is_reasoning: Filter by whether model supports reasoning
		supports_vision: Filter by whether model supports image input
		preference: Optional model name preference - will try to match this first

	Returns:
		Name of first matching model, or None if no models match criteria
	"""
	models = get_models(
		provider=provider,
		size=size,
		is_reasoning=is_reasoning,
		supports_vision=supports_vision,
	)

	if not models:
		return None

	if preference:
		models = [model for model in models if preference.lower() in model.lower()] or models

	return models[0]


@cache(ttl=60)
def get_models(
	*,
	provider: Provider | None = None,
	size: ModelSize | None = None,
	is_reasoning: bool | None = None,
	supports_vision: bool | None = None,
) -> list[str]:
	"""Returns a list of available models matching the given criteria.

	This function checks both the model capabilities and provider availability.
	Models are only returned if their provider's API key is configured and valid.

	Args:
		provider: Filter by specific provider (OpenAI, Anthropic, etc)
		size: Filter by model size (Very Small, Small, Medium, Large)
		is_reasoning: Filter by whether model supports reasoning
		supports_vision: Filter by whether model supports image input

	Returns:
		List of model names that match all criteria and are available for use
	"""
	if provider and not is_provider_available(provider):
		return []

	filters: dict[str, Any] = {"enabled": True}
	if provider is not None:
		filters["provider"] = provider

	if size is not None:
		filters["size"] = size

	if is_reasoning is not None:
		filters["is_reasoning"] = is_reasoning

	if supports_vision is not None:
		filters["supports_vision"] = supports_vision

	models = frappe.get_all("Otto LLM", filters=filters, pluck="name")
	if provider:
		return models

	available: list[str] = []
	availability: dict[Provider, bool] = {}
	for model in models:
		provider = utils.get_provider(model)
		if not provider:
			continue

		if provider not in availability:
			availability[provider] = is_provider_available(provider)

		if availability[provider]:
			available.append(model)

	return available
