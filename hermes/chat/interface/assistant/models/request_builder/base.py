import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from hermes.chat.interface.assistant.models.prompt_builder.base import PromptBuilderFactory
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.messages import (
    AudioFileMessage,
    EmbeddedPDFMessage,
    ImageMessage,
    ImageUrlMessage,
    InvisibleMessage,
    LLMRunCommandOutput,
    Message,
    TextGeneratorMessage,
    TextMessage,
    TextualFileMessage,
    ThinkingAndResponseGeneratorMessage,
    UrlMessage,
    VideoMessage,
)
from hermes.utils.file_reader import FileReader

logger = logging.getLogger(__name__)

"""
RequestBuilder is responsible for building the actual API request to the LLM provider.
It should be able to handle all the model details, the API requirements,
translate the internal message format to the provider's message format.
"""


class RequestBuilder(ABC):
    def __init__(
        self,
        model_tag: str,
        notifications_printer: CLINotificationsPrinter,
        prompt_builder_factory: PromptBuilderFactory,
    ):
        self.model_tag = model_tag
        self.notifications_printer = notifications_printer
        self.prompt_builder_factory = prompt_builder_factory

        self._url_contents = {}

    def build_request(self, messages: Sequence[Message]) -> Any:
        """Build a request for the LLM provider from a sequence of messages.

        Args:
            messages: A sequence of Message objects to include in the request.

        Returns:
            A provider-specific request object.
        """
        self.initialize_request()

        for message in messages:
            self._process_message(message)

        return self.compile_request()

    def _process_message(self, message: Message) -> None:
        """Process a single message and delegate to the appropriate handler.

        Args:
            message: The Message object to process.
        """
        # Use dedicated methods for handling different message types
        handler = self._get_message_handler(message)
        if handler:
            handler(message)
        else:
            self.notifications_printer.print_error(f"Unsupported message type: {type(message)}. Discarding message.")

    def _get_message_handler(self, message: Message):
        """Determine the appropriate handler method for the given message type.

        Args:
            message: The Message object to find a handler for.

        Returns:
            A method to handle the message or None if no handler is found.
        """
        message_type_map = self._get_message_type_handler_map()

        # Check direct type matches first
        for message_type in message_type_map:
            if isinstance(message, message_type):
                return message_type_map[message_type]

        # Check for grouped message types
        for types, handler in message_type_map.items():
            if isinstance(types, tuple) and isinstance(message, types):
                return handler

        return None

    def _get_message_type_handler_map(self):
        """Returns a mapping of message types to their handler methods."""
        return {
            TextMessage: self._process_text_message,
            # Group similar message types with the same handler
            (TextGeneratorMessage, ThinkingAndResponseGeneratorMessage, InvisibleMessage): self._process_text_generator_message,
            ImageUrlMessage: self._process_image_url_message,
            ImageMessage: self._process_image_message,
            AudioFileMessage: self._process_audio_file_message,
            VideoMessage: self._process_video_message,
            EmbeddedPDFMessage: self._process_embedded_pdf_message,
            TextualFileMessage: self._process_textual_file_message,
            UrlMessage: self._process_url_message,
            LLMRunCommandOutput: self._process_llm_run_command_output,
        }

    def handle_text_message(
        self,
        text: str,
        author: str,
        message_id: int,
        name: str | None = None,
        text_role: str | None = None,
    ):
        self.notifications_printer.print_error(f"Text message not supported by {self.model_tag}. Discarding message.")

    def handle_image_url_message(self, url: str, author: str, message_id: int):
        self.notifications_printer.print_error(f"Image URL message not supported by {self.model_tag}. Discarding message.")

    def handle_image_message(self, image_path: str, author: str, message_id: int):
        self.notifications_printer.print_error(f"Image message not supported by {self.model_tag}. Discarding message.")

    def handle_audio_file_message(self, audio_path: str, author: str, message_id: int):
        self.notifications_printer.print_error(f"Audio file message not supported by {self.model_tag}. Discarding message.")

    def handle_video_message(self, video_path: str, author: str, message_id: int):
        self.notifications_printer.print_error(f"Video message not supported by {self.model_tag}. Discarding message.")

    def handle_embedded_pdf_message(self, pdf_path: str, pages: list[int], author: str, message_id: int):
        self.notifications_printer.print_error(f"PDF message not supported by {self.model_tag}. Discarding message.")

    def handle_textual_file_message(
        self,
        text_filepath: str,
        author: str,
        message_id: int,
        file_role: str | None = None,
    ):
        self.notifications_printer.print_error(f"Textual file message not supported by {self.model_tag}. Discarding message.")

    def handle_llm_run_command_output(self, text: str, author: str, message_id: int, name: str | None = None):
        """Handle LLM-run command output messages by converting them to text messages with CommandExecutionOutput role"""
        self.handle_text_message(
            text=text,
            author=author,
            message_id=message_id,
            name=name,
            text_role="CommandExecutionOutput",
        )

    def handle_url_message(self, url: str, author: str, message_id: int):
        self.notifications_printer.print_error(f"URL message not supported by {self.model_tag}. Discarding message.")

    @abstractmethod
    def compile_request(self) -> Any:
        pass

    @abstractmethod
    def initialize_request(self):
        pass

    def _default_handle_url_message(self, url: str, author: str, message_id: int):
        """Get the content of the URL, convert the HTML to markdown and send it as a text message
        Use requests to get the content of the URL.
        """
        markdown_content = self._get_url_text_content(url, message_id)
        if markdown_content is not None:
            self.handle_text_message(markdown_content, author, message_id, name=url, text_role="webpage")

    def _get_url_text_content(self, url: str, message_id: int) -> str:
        if message_id in self._url_contents:
            return self._url_contents[message_id]
        try:
            import requests
            from markitdown import MarkItDown

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            markitdown = MarkItDown()
            conversion_result = markitdown.convert(response)
            markdown_content = conversion_result.text_content
            if not markdown_content:
                markdown_content = "No content found in the URL"
                self.notifications_printer.print_error(f"No content found in the URL {url}")
            self._url_contents[message_id] = markdown_content
            return markdown_content
        except Exception as e:
            self.notifications_printer.print_error(f"Error fetching URL {url}: {e}")
            placeholder_content = f"Error getting the contents of the URL {url}"
            self._url_contents[message_id] = placeholder_content
            return placeholder_content

    def _get_url_image_content(self, url: str, message_id: int):
        if message_id in self._url_contents:
            return self._url_contents[message_id]
        try:
            import requests

            response = requests.get(url)
            response.raise_for_status()
            content = response.content
            self._url_contents[message_id] = content
            return content
        except Exception as e:
            self.notifications_printer.print_error(f"Error fetching URL {url}: {e}")
            self._url_contents[message_id] = None
            return None

    def _default_handle_textual_file_message(
        self,
        text_filepath: str,
        author: str,
        message_id: int,
        file_role: str | None = None,
    ):
        """Read the content of the file or traverse directory, and create text messages with the content.
        For files, use filepath as name and 'textual_file' as role.
        For directories, process each file recursively.
        """
        if os.path.isdir(text_filepath):
            # Process directory contents
            self._process_directory(text_filepath, author, message_id, file_role)
            return

        # If it's a single file, process it directly
        self._process_single_file(text_filepath, author, message_id, file_role)

    def _process_single_file(
        self,
        text_filepath: str,
        author: str,
        message_id: int,
        file_role: str | None = None,
    ):
        """Process a single file and send its content as a message."""
        # Use the shared FileReader utility to get file content
        file_content, success = FileReader.read_file(text_filepath)

        if success:
            role = self._determine_file_role(text_filepath, file_role)

            # Handle the message with the content
            self.handle_text_message(
                text=file_content,
                author=author,
                message_id=message_id,
                name=text_filepath,
                text_role=role,
            )
        else:
            # Handle error case
            self.notifications_printer.print_error(f"Failed to read file: {text_filepath}")
            self.handle_text_message(
                text=file_content,  # This will contain the error message
                author=author,
                message_id=message_id,
                name=text_filepath,
                text_role="ErrorReadingFile",
            )

    def _process_directory(self, directory_path: str, author: str, message_id: int, file_role: str | None = None):
        """Process all files in a directory and send their content as messages."""
        # Use FileReader to process the entire directory
        file_contents = FileReader.read_directory(directory_path)

        # Process each file in the directory
        for relative_path, content in file_contents.items():
            full_path = os.path.join(directory_path, relative_path)
            try:
                # Use the content we already read
                role = self._determine_file_role(full_path, file_role)

                self.handle_text_message(
                    text=content,
                    author=author,
                    message_id=message_id,
                    name=full_path,
                    text_role=role,
                )
            except Exception as e:
                self.notifications_printer.print_error(f"Error processing file {full_path}: {e}")

    def _determine_file_role(self, file_path: str, base_file_role: str | None = None) -> str:
        """Determine the appropriate role for a file based on its type and any provided base role."""
        role = "TextualFile"
        if file_path.endswith(".ipynb"):
            role = "JupyterNotebook"

        if base_file_role:
            role = f"{role} with role={base_file_role}"

        return role

    def _extract_pages_from_pdf(self, pdf_path: str, pages: list[int]) -> str:
        """Extract the specified pages from the PDF, create a temporary pdf file with the extracted pages and return the path
        to the temporary file.
        If a given page is not present, skip it.
        """
        try:
            import tempfile

            from PyPDF2 import PdfReader, PdfWriter

            # Create a PDF reader object
            reader = PdfReader(pdf_path)
            writer = PdfWriter()

            # Get total pages in the PDF
            total_pages = len(reader.pages)

            # Add requested pages to the writer
            for page_num in pages:
                # Convert to 0-based index and check if page exists
                idx = page_num - 1
                if 0 <= idx < total_pages:
                    writer.add_page(reader.pages[idx])
                else:
                    self.notifications_printer.print_error(f"Page {page_num} not found in PDF. Skipping.")

            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as temp_file:
                temp_path = temp_file.name
                writer.write(temp_file)

            return temp_path

        except Exception as e:
            self.notifications_printer.print_error(f"Error extracting pages from PDF {pdf_path}, sending whole file: {e}")
            return pdf_path  # Return original file path if extraction fails

    def _process_text_message(self, message: TextMessage) -> None:
        """Process a text message."""
        content = message.get_content_for_assistant()
        if content:
            content = content.strip()
            if content:
                self.handle_text_message(
                    text=content,
                    author=message.author,
                    message_id=id(message),
                    name=message.name,
                    text_role=message.text_role,
                )

    def _process_text_generator_message(
        self, message: TextGeneratorMessage | ThinkingAndResponseGeneratorMessage | InvisibleMessage
    ) -> None:
        """Process a text generator, thinking and response, or invisible message."""
        content = message.get_content_for_assistant()
        if content:
            content = content.strip()
            if content:
                self.handle_text_message(
                    content,
                    message.author,
                    id(message),
                    message.name,
                    message.text_role,
                )

    def _process_image_url_message(self, message: ImageUrlMessage) -> None:
        """Process an image URL message."""
        content = message.get_content_for_assistant()
        if content:
            self.handle_image_url_message(content, message.author, id(message))

    def _process_image_message(self, message: ImageMessage) -> None:
        """Process an image message."""
        content = message.get_content_for_assistant()
        if content:
            self.handle_image_message(content, message.author, id(message))

    def _process_audio_file_message(self, message: AudioFileMessage) -> None:
        """Process an audio file message."""
        content = message.get_content_for_assistant()
        if content:
            self.handle_audio_file_message(content, message.author, id(message))

    def _process_video_message(self, message: VideoMessage) -> None:
        """Process a video message."""
        content = message.get_content_for_assistant()
        if content:
            self.handle_video_message(content, message.author, id(message))

    def _process_embedded_pdf_message(self, message: EmbeddedPDFMessage) -> None:
        """Process an embedded PDF message."""
        content = message.get_content_for_assistant()
        if content:
            self.handle_embedded_pdf_message(
                content["pdf_filepath"],
                content["pages"],
                message.author,
                id(message),
            )

    def _process_textual_file_message(self, message: TextualFileMessage) -> None:
        """Process a textual file message."""
        content = message.get_content_for_assistant()
        if content["textual_content"]:
            self.handle_text_message(
                content["textual_content"],
                message.author,
                id(message),
                name=message.name,
                text_role=message.file_role,
            )
        elif content["text_filepath"]:
            self.handle_textual_file_message(
                content["text_filepath"],
                message.author,
                id(message),
                file_role=message.file_role,
            )

    def _process_url_message(self, message: UrlMessage) -> None:
        """Process a URL message."""
        content = message.get_content_for_assistant()
        if content:
            self.handle_url_message(content, message.author, id(message))

    def _process_llm_run_command_output(self, message: LLMRunCommandOutput) -> None:
        """Process an LLM run command output message."""
        content = message.get_content_for_assistant()
        if content:
            self.handle_llm_run_command_output(
                text=content,
                author=message.author,
                message_id=id(message),
                name=message.name,
            )
