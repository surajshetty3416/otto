from __future__ import annotations

from otto import utils
from otto.lib.types import FileContent, ImageContent, TextContent


class content:
	"""
	Convenience class for creating `UserContent` objects.

	Examples:
	```python
	from otto.lib import content
	from otto.lib import quick_query

	# Create a list of user content objects
	user_content = [
	    # Text content
	    content.text("Hello, can you explain these images and files?"),
	    # Image content from url
	    content.image("https://example.com/image.png"),
	    # File content
	    content.file("base64_encoded_pdf_data", name="document.pdf),
	    # Image content from data
	    content.image("data:image/png;base64,..."),
	]


	# Call the LLM
	res = quick_query(user_content)
	```
	"""

	@staticmethod
	def text(query: str) -> TextContent:
		"""
		Create a text content object.

		Args:
			query: The text to be displayed.
		"""
		return TextContent(type="text", text=query)

	@staticmethod
	def image(value: str) -> ImageContent:
		"""
		Create an image content object from various sources.

		Args:
			value: The image source, which can be:
				- HTTP/HTTPS URL (e.g., "https://example.com/image.png")
				- Data URI (e.g., "data:image/png;base64,...")
				- Frappe File document name or file URL
				- Local file path
		"""
		f = utils.get_file(value, get_data_if_url=False)
		if f.is_url:
			return ImageContent(type="image", url=f.value, data=None)
		return ImageContent(type="image", data=f.value, url=None)

	@staticmethod
	def file(value: str, name: str | None = None) -> FileContent:
		"""
		Create a file content object from various sources.

		Args:
			value: The file source, which can be:
				- HTTP/HTTPS URL (e.g., "https://example.com/document.pdf")
				- Data URI (e.g., "data:application/pdf;base64,...")
				- Frappe File document name or file URL
				- Local file path
			name: The name of the file. If not provided, will be inferred from the source.
		"""
		f = utils.get_file(value, get_data_if_url=True)
		return FileContent(
			type="file",
			name=name or f.name or "file.pdf",
			data=f.value,
		)
