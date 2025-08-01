# Otto Lib

Library for adding LLM capabilities into Frappe apps.

> [!NOTE]
>
> Otto Lib is meant to be used specifically with Frappe apps. The library
> features offered by Otto are backed by DocTypes in Otto and so cannot be
> provided as a standalone library.

## Index

- [Example](#example)
- [Installation](#installation)
- [Sessions](./session.md)
- [Models](./model.md)

## Overview

If you're attempting to build LLM features into your Frappe app where:

- The user is given control over what models to choose, across multiple providers
- The user is allowed to update system prompts or instructions to better fit their need
- The user would like to track their LLM usage

Then Otto Lib is a suitable library to use. This library exposes Otto's core LLM
functionality allowing you to build custom LLM features around it.

Using this library allows Otto to manage:

1. [Sessions](./session.md):

   - Manage state of turn based or one shot LLM interactions.
   - Keep track of all LLM interactions.
   - View stats and analytics across all LLM interactions.

2. [Models](./model.md):
   - Use multiple model provders without having to deal with their individual APIs.
   - Use models that the user has access to.
   - Discover available models.

## Example

```python
import otto.lib as otto

# 1. Get available model that matches criteria
model = otto.get_model(provider="Anthropic", is_reasoning=True)


# 2. Quick one-off query
response = otto.quick_query("Hello, world!", model=model, stream=False)
print(response[0]["text"])


# 3. Session-based interaction
session = otto.new(model=model, instruction="You are a helpful assistant")
for chunk in session.interact("What's the weather like?"):
    print(chunk.get("text", ""), end="")


# 4. Load existing session and continue interaction
session = otto.load(session_id)
response, _ = session.interact("What was the last thing I told you?", stream=False)
print(response[0]["text"])


# 5. Model discovery
available_models = otto.get_models(provider="Google", size="Large")
```

## Installation

Otto is a Frappe application and to use Otto Lib, Otto needs to be installed
along side your Frappe application ([docs](https://docs.frappe.io/framework/user/en/guides/basics/apps#adding-app-to-a-site)).

```bash
# In your bench folder
bench get-app https://github.com/frappe/otto

# Install the app on your site
bench --site site_name install-app otto
```

If you wish to make LLM features in your app available _as an option_, you can
check if it's available before using like so:

```python
try:
    import otto.lib as otto
except ImportError:
    otto = None


def llm_feature_in_your_app(...):
    if otto is None:
        return

    session = otto.new(...) # use session to implement feature
```

<!--
Point to implementation in other apps as example once done.
-->
