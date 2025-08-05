# Models

Model discovery, creation, and availability utilities.

Model management in Otto is backed by the `OttoLLM` DocType. This keeps track of
all the models available to the user along with their capabilities.

Otto creates default entries when its installed
([ref](https://github.com/frappe/otto/blob/develop/otto/fixtures/otto_llm.json)),
the user is free to enable or disable these models. If the models required by
your apps aren't available you may create them.

- [Example](#example)
- [Reference](#reference)

## Example

A short example that illustrates how the utils in model may be used.

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

## Reference

- [`is_model_available`](#is_model_available): Check if a specific model is available for usage
- [`is_provider_available`](#is_provider_available): Check if a specific provider is available for usage
- [`create_model`](#create_model): Create new model entries with specific configuration
- [`get_model`](#get_model): Find the first model matching criteria with optional preference
- [`get_models`](#get_models): Get all models matching specified filters
- [`set_api_key`](#set_api_key): Set the API key for a provider

> [!TIP]
>
> It is recommended to view the source code
> ([ref](https://github.com/frappe/otto/blob/develop/otto/lib/model.py)) for
> the methods or functions that you need to use as it is well documented.
>
> Since most functions and methods are well typed, you can use your IDE's view
> definition feature to get accurate info on the signature and return types.
>
> Type definitions are in
> [otto.lib.types](https://github.com/frappe/otto/blob/develop/otto/lib/types.py)
> and
> [otto.llm.types](https://github.com/frappe/otto/blob/develop/otto/llm/types.py).

### `is_model_available`

Checks if a given model name is available in Otto LLM. This function checks if a model exists and is enabled in the Otto LLM system. The check can be done either with exact matching or partial name matching.

```python
def is_model_available(model: str, exact: bool = True) -> bool
```

**Example:**

```python
import otto.lib as otto

# Check for exact model name match
if otto.is_model_available("anthropic/claude-3-5-haiku-latest"):
    print("Model is available")

# Check for partial match (case insensitive)
if otto.is_model_available("claude", exact=False):
    print("Found a Claude model")

# Check for disabled models (returns False)
if not otto.is_model_available("openai/o3"):
    print("Model is not available or disabled")
```

### `is_provider_available`

Returns `True` if the provider is available. This checks if the provider's API key is configured and valid.

```python
def is_provider_available(provider: Provider) -> bool
```

**Example:**

```python
import otto.lib as otto

# Check if provider has valid API key
if otto.is_provider_available("OpenAI"):
    print("OpenAI is available for use")

if otto.is_provider_available("Anthropic"):
    print("Anthropic is available for use")

if not otto.is_provider_available("Google"):
    print("Google provider not available - check API key")
```

### `create_model`

Creates a new Otto LLM entry with the specified parameters. Returns the name of the created model in format "{provider_id}/{provider_model_id}".

```python
def create_model(
    *,
    title: str,
    provider: Provider,
    provider_model_id: str,
    size: ModelSize,
    is_reasoning: bool,
    supports_vision: bool,
) -> str
```

**Example:**

```python
import otto.lib as otto

# Create a new OpenAI model
model_name = otto.create_model(
    title="GPT-4.1 Nano Test",
    provider="OpenAI",
    provider_model_id="gpt-4.1-nano-2025-04-14",
    size="Very Small",
    is_reasoning=False,
    supports_vision=True,
)
# Returns: "openai/gpt-4.1-nano-2025-04-14"

# Create a new Anthropic model
anthropic_model = otto.create_model(
    title="Claude 4 Sonnet",
    provider="Anthropic",
    provider_model_id="claude-sonnet-4-20250514",
    size="Large",
    is_reasoning=True,
    supports_vision=True,
)
# Returns: "anthropic/claude-sonnet-4-20250514"

# Create a new Google model
google_model = otto.create_model(
    title="Gemini 2.5 Flash",
    provider="Google",
    provider_model_id="gemini-2.5-flash",
    size="Medium",
    is_reasoning=False,
    supports_vision=True,
)
# Returns: "gemini/gemini-2.5-flash"
```

### `get_model`

Returns the first available model matching the given criteria. `preference` can be used to specify a model name that is preferred - if available this will be returned, otherwise a model matching the rest of the criteria will be returned.

```python
def get_model(
    *,
    provider: Provider | None = None,
    size: ModelSize | None = None,
    is_reasoning: bool | None = None,
    supports_vision: bool | None = None,
    preference: str | None = None,
) -> str | None
```

**Example:**

```python
import otto.lib as otto

# Get any available model with preference
model = otto.get_model(preference="claude")
# Returns first available Claude model

# Get model with specific criteria and preference
model = otto.get_model(
    provider="OpenAI",
    is_reasoning=True,
    preference="o1-preview"
)
# Returns "openai/o1-preview" if available, else any OpenAI reasoning model

# Get model by criteria only
model = otto.get_model(
    provider="Anthropic",
    size="Large",
    supports_vision=True
)
# Returns first available large Anthropic model with vision support
```

### `get_models`

Returns a list of available models matching the given criteria. This function checks both the model capabilities and provider availability. Models are only returned if their provider's API key is configured and valid.

```python
def get_models(
    *,
    provider: Provider | None = None,
    size: ModelSize | None = None,
    is_reasoning: bool | None = None,
    supports_vision: bool | None = None,
) -> list[str]
```

**Example:**

```python
import otto.lib as otto

# Get all models from a specific provider
anthropic_models = otto.get_models(provider="Anthropic")
# Returns: ["anthropic/claude-3-5-haiku-latest", "anthropic/claude-3-5-sonnet-20241022", ...]

# Get models by size
small_models = otto.get_models(size="Small")
# Returns all enabled small models

# Get reasoning models
reasoning_models = otto.get_models(is_reasoning=True)
# Returns all models with reasoning capabilities

# Get models with multiple criteria
filtered_models = otto.get_models(
    provider="OpenAI",
    size="Medium",
    supports_vision=True
)
# Returns medium sized OpenAI models that support vision
```

### `set_api_key`

Sets the API key for a provider. This configures the API key that Otto will use to authenticate with the specified provider.

```python
def set_api_key(provider: Provider, value: str) -> None
```

**Example:**

```python
import otto.lib as otto

# Set OpenAI API key
otto.set_api_key("OpenAI", "sk-your-openai-api-key-here")

# Set Anthropic API key
otto.set_api_key("Anthropic", "sk-ant-your-anthropic-key-here")

# Set Google API key
otto.set_api_key("Google", "your-gemini-api-key-here")

# Verify provider is now available
if otto.is_provider_available("OpenAI"):
    print("OpenAI API key successfully configured")
```
