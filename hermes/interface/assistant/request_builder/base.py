from abc import ABC, abstractmethod
from typing import Callable

from hermes_beta.interface.assistant.prompt_builder.base import PromptBuilder, PromptBuilderFactory
from hermes_beta.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes_beta.message import AudioFileMessage, AutoRedactedInvisibleTextMessage, EmbeddedPDFMessage, ImageMessage, ImageUrlMessage, InvisibleMessage, Message, TextGeneratorMessage, TextMessage, TextualFileMessage, UrlMessage, VideoMessage

"""
RequestBuilder is responsible for building the actual API request to the LLM provider.
It should be able to handle all the model details, the API requirements, translate the internal message format to the provider's message format.
"""
class RequestBuilder(ABC):
    def __init__(self, model_tag: str, notifications_printer: CLINotificationsPrinter, prompt_builder_factory: PromptBuilderFactory):
        self.model_tag = model_tag
        self.notifications_printer = notifications_printer
        self.prompt_builder_factory = prompt_builder_factory

    def build_request(self, messages: list[Message]) -> any:
        self.initialize_request()

        for message in messages:
            if isinstance(message, TextMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, TextGeneratorMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, InvisibleMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, AutoRedactedInvisibleTextMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, ImageUrlMessage):
                self.handle_image_url_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, ImageMessage):
                self.handle_image_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, AudioFileMessage):
                self.handle_audio_file_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, VideoMessage):
                self.handle_video_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, EmbeddedPDFMessage):
                self.handle_embedded_pdf_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, TextualFileMessage):
                self.handle_textual_file_message(message.get_content_for_assistant(), message.author)
            elif isinstance(message, UrlMessage):
                self.handle_url_message(message.get_content_for_assistant(), message.author)
            else:
                self.notifications_printer.print_error(f"Unsupported message type: {type(message)}. Discarding message.")
                continue
        
        return self.compile_request()
    
    def handle_text_message(self, text: str, author: str):
        self.notifications_printer.print_error(f"Text message not supported by {self.model_tag}. Discarding message.")

    def handle_image_url_message(self, url: str, author: str):
        self.notifications_printer.print_error(f"Image URL message not supported by {self.model_tag}. Discarding message.")

    def handle_image_message(self, image_path: str, author: str):
        self.notifications_printer.print_error(f"Image message not supported by {self.model_tag}. Discarding message.")

    def handle_audio_file_message(self, audio_path: str, author: str):
        self.notifications_printer.print_error(f"Audio file message not supported by {self.model_tag}. Discarding message.")

    def handle_video_message(self, video_path: str, author: str):
        self.notifications_printer.print_error(f"Video message not supported by {self.model_tag}. Discarding message.")

    def handle_embedded_pdf_message(self, pdf_path: str, author: str):
        self.notifications_printer.print_error(f"PDF message not supported by {self.model_tag}. Discarding message.")

    def handle_textual_file_message(self, text_filepath: str, author: str):
        self.notifications_printer.print_error(f"Textual file message not supported by {self.model_tag}. Discarding message.")

    def handle_url_message(self, url: str, author: str):
        self.notifications_printer.print_error(f"URL message not supported by {self.model_tag}. Discarding message.")

    @abstractmethod
    def compile_request(self) -> any:
        pass

    @abstractmethod
    def initialize_request(self):
        pass

    def _default_handle_url_message(self, url: str, author: str):
        """
        Get the content of the URL, convert the HTML to markdown and send it as a text message
        Use requests to get the content of the URL.
        """
        import requests

        try:
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text
            markdown_content = self._convert_html_to_markdown(html_content)
            self.handle_text_message(markdown_content, author)
        except requests.RequestException as e:
            self.notifications_printer.print_error(f"Error fetching URL {url}: {e}")

    def _convert_html_to_markdown(self, html: str) -> str:
        from markdownify import markdownify as md
        try:
            markdown = md(html)
            return markdown
        except Exception as e:
            # Handle or log the exception as needed
            print(f"Error converting HTML to Markdown, falling back to raw HTML: {e}")
            return html

    def _default_handle_textual_file_message(self, text_filepath: str, author: str):
        """
        Read the content of the file, and create a text message with the content of the file
        Then use .handle_text_message
        """
        try:
            with open(text_filepath, 'r', encoding='utf-8') as file:
                file_content = file.read()
                self.handle_text_message(file_content, author)
        except Exception as e:
            self.notifications_printer.print_error(f"Error reading file {text_filepath}: {e}")
