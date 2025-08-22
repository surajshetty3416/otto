# Utilities

Utility functions to help with common tasks.

## Reference

- [`content`](#content): Set of static methods for creating `UserContent` objects.
  - [`content.text`](#contenttext): Create a text content object.
  - [`content.image`](#contentimage): Create an image content object from various sources.
  - [`content.file`](#contentfile): Create a file content object from various sources.

> [!TIP]
>
> It is recommended to view the source code
> ([ref](https://github.com/frappe/otto/blob/develop/otto/lib/utils.py)) for
> the methods or functions that you need to use as it is well documented.
>
> Since most functions and methods are well typed, you can use your IDE's view
> definition feature to get accurate info on the signature and return types.
>
> Type definitions are in
> [otto.lib.types](https://github.com/frappe/otto/blob/develop/otto/lib/types.py)
> and
> [otto.llm.types](https://github.com/frappe/otto/blob/develop/otto/llm/types.py).

### `content`

Provides static methods to create different types of content (text, images, files) from various sources.

When using `otto.quick_query` or `session.interact` you need to provide a query. This query may be a string, an image, a file or a combination of these passed as a list. Check the `Query` type in [types.py](https://github.com/frappe/otto/blob/develop/otto/llm/types.py) for more details.

The `content` class provides a convenient way to create this list of content objects.

```python
import otto.lib as otto
from otto.lib import content

# Create a list of user content objects
user_content = [
    # Text content
    content.text("Hello, can you explain these images and files?"),

    # Image content from url
    content.image("https://example.com/image.png"),

    # File content
    content.file("data:application/pdf;base64,...", name="document.pdf"),

    # Image content from data
    content.image("data:image/png;base64,..."),
]


# Call the LLM
res = otto.quick_query(user_content)
```

#### `content.text`

Create a text content object for use in LLM queries.

```python
def text(query: str) -> TextContent
```

**Parameters:**

- `query`: The text to be displayed.

**Returns:**

- `ImageContent`: An image content object that can be used in user queries.

**Example:**

```python
from otto.lib import content

text_content = content.text("Hello, can you help me with this question?")
```

#### `content.image`

Create an image content object from various sources including URLs, data URIs, Frappe File entries, or local file paths.

```python
def image(value: str) -> ImageContent
```

**Parameters:**

- `value`: The image source, which can be:
  - HTTP/HTTPS URL (e.g., `"https://example.com/image.png"`)
  - Data URI (e.g., `"data:image/png;base64,..."`)
  - Frappe File document name or File URL
  - Local file path

**Returns:**

- `ImageContent`: An image content object that can be used in user queries.

**Example:**

```python
from otto.lib import content

# From URL
image_from_url = content.image("https://example.com/chart.png")

# From data URI
image_from_data = content.image("data:image/png;base64,...")

# From a Frappe File doc
image_from_file = content.image("9d0b52933f")
```

#### `content.file`

Create a file content object from various sources including URLs, data URIs, Frappe File documents, or local file paths.

```python
def file(value: str, name: str | None = None) -> FileContent
```

**Parameters:**

- `value`: The file source, which can be:
  - HTTP/HTTPS URL (e.g., `"https://example.com/document.pdf"`)
  - Data URI (e.g., `"data:application/pdf;base64,..."`)
  - Frappe File document name or file URL
  - Local file path
- `name`: Optional name for the file. If not provided, will be inferred from the source or will be set to `file.pdf`.

**Returns:**

- `FileContent`: A file content object that can be used in user queries.

**Example:**

```python
from otto.lib import content

# From URL with custom name
pdf_content = content.file("https://example.com/report.pdf", name="monthly_report.pdf")

# From data URI
file_from_data = content.file("data:application/pdf;base64,JVBERi0xLjQKJcOkw7...", name="document.pdf")

# From Frappe File (name will be inferred)
file_from_frappe = content.file("8e0b52933f")
```
