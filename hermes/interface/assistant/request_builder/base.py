from abc import ABC, abstractmethod
from typing import Callable

from hermes.interface.assistant.prompt_builder.base import PromptBuilder, PromptBuilderFactory
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.message import AudioFileMessage, AutoRedactedInvisibleTextMessage, EmbeddedPDFMessage, ImageMessage, ImageUrlMessage, InvisibleMessage, Message, TextGeneratorMessage, TextMessage, TextualFileMessage, UrlMessage, VideoMessage

"""
RequestBuilder is responsible for building the actual API request to the LLM provider.
It should be able to handle all the model details, the API requirements, translate the internal message format to the provider's message format.
"""
class RequestBuilder(ABC):
    def __init__(self, model_tag: str, notifications_printer: CLINotificationsPrinter, prompt_builder_factory: PromptBuilderFactory):
        self.model_tag = model_tag
        self.notifications_printer = notifications_printer
        self.prompt_builder_factory = prompt_builder_factory

        self._url_contents = {}

    def build_request(self, messages: list[Message]) -> any:
        self.initialize_request()

        for message in messages:
            if isinstance(message, TextMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, TextGeneratorMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, InvisibleMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, AutoRedactedInvisibleTextMessage):
                self.handle_text_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, ImageUrlMessage):
                self.handle_image_url_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, ImageMessage):
                self.handle_image_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, AudioFileMessage):
                self.handle_audio_file_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, VideoMessage):
                self.handle_video_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, EmbeddedPDFMessage):
                pdf_details = message.get_content_for_assistant()
                self.handle_embedded_pdf_message(pdf_details["pdf_filepath"], pdf_details["pages"], message.author, id(message))
            elif isinstance(message, TextualFileMessage):
                self.handle_textual_file_message(message.get_content_for_assistant(), message.author, id(message))
            elif isinstance(message, UrlMessage):
                self.handle_url_message(message.get_content_for_assistant(), message.author, id(message))
            else:
                self.notifications_printer.print_error(f"Unsupported message type: {type(message)}. Discarding message.")
                continue
        
        return self.compile_request()
    
    def handle_text_message(self, text: str, author: str, message_id: int):
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

    def handle_textual_file_message(self, text_filepath: str, author: str, message_id: int):
        self.notifications_printer.print_error(f"Textual file message not supported by {self.model_tag}. Discarding message.")

    def handle_url_message(self, url: str, author: str, message_id: int):
        self.notifications_printer.print_error(f"URL message not supported by {self.model_tag}. Discarding message.")

    @abstractmethod
    def compile_request(self) -> any:
        pass

    @abstractmethod
    def initialize_request(self):
        pass

    def _default_handle_url_message(self, url: str, author: str, message_id: int):
        """
        Get the content of the URL, convert the HTML to markdown and send it as a text message
        Use requests to get the content of the URL.
        """

        markdown_content = self._get_url_text_content(url, message_id)
        if markdown_content is not None:
            self.handle_text_message(markdown_content, author, message_id)
    
    def _get_url_text_content(self, url: str, message_id: int) -> str:
        if message_id in self._url_contents:
            return self._url_contents[message_id]
        try:
            import requests
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text
            markdown_content = self._convert_html_to_markdown(html_content)
            self._url_contents[message_id] = markdown_content
            return markdown_content
        except Exception as e:
            self.notifications_printer.print_error(f"Error fetching URL {url}: {e}")
            self._url_contents[message_id] = None
            return None
    
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

    def _convert_html_to_markdown(self, html: str) -> str:
        from markdownify import markdownify as md
        try:
            markdown = md(html)
            return markdown
        except Exception as e:
            # Handle or log the exception as needed
            print(f"Error converting HTML to Markdown, falling back to raw HTML: {e}")
            return html

    def _default_handle_textual_file_message(self, text_filepath: str, author: str, message_id: int):
        """
        Read the content of the file, and create a text message with the content of the file
        Then use .handle_text_message
        """
        try:
            file_identifier = f"// Content of file {text_filepath}\n"
            with open(text_filepath, 'r', encoding='utf-8') as file:
                file_content = file.read()
                file_content = file_identifier + file_content
                self.handle_text_message(file_content, author, message_id)
        except Exception as e:
            self.notifications_printer.print_error(f"Error reading file {text_filepath}: {e}")

    def _extract_pages_from_pdf(self, pdf_path: str, pages: list[int]) -> str:
        """
        Extract the specified pages from the PDF, create a temporary pdf file with the extracted pages and return the path to the temporary file.
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
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_path = temp_file.name
            
            # Write the selected pages to the temporary file
            with open(temp_path, 'wb') as output_file:
                writer.write(output_file)
                
            return temp_path
            
        except Exception as e:
            self.notifications_printer.print_error(f"Error extracting pages from PDF {pdf_path}, sending whole file: {e}")
            return pdf_path  # Return original file path if extraction fails