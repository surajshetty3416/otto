# Model

Model discovery, creation, and availability utilities.

## Exports

- [`is_model_available`](#is_model_available): Check if a specific model is available for usage
- [`is_provider_available`](#is_provider_available): Check if a specific provider is available for usage
- [`create_model`](#create_model): Create new model entries with specific configuration
- [`get_model`](#get_model): Find the first model matching criteria with optional preference
- [`get_models`](#get_models): Get all models matching specified filters
- [`set_api_key`](#set_api_key): Set the API key for a provider

## Example

```python
import otto.lib as otto

# Check if specific model exists
if otto.is_model_available("claude-3-5-sonnet"):
    print("Model is available")

# Get all large reasoning models
reasoning_models = otto.get_models(size="Large", is_reasoning=True, provider="Anthropic")

# Create a new model
model_name = otto.create_model(
    title="Claude 4 Sonnet",
    provider="Anthropic",
    provider_model_id="claude-sonnet-4-20250514",
    size="Medium",
    is_reasoning=True,
    supports_image=True,
)

# Get preferred model with fallback
model = otto.get_model(
    provider="OpenAI",
	is_reasoning=True,
    preference="o1-preview",  # Will try this first, fallback to any OpenAI reasoning model
)
```

## Provider model ID references:

- Anthropic: https://docs.anthropic.com/en/docs/about-claude/models/overview#model-names
- OpenAI: https://platform.openai.com/docs/models
- Gemini: https://ai.google.dev/gemini-api/docs/models#model-variations

## Methods

### `is_model_available`

### `is_provider_available`

### `create_model`

### `get_model`

### `get_models`

### `set_api_key`
