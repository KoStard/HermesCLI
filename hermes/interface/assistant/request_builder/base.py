from abc import ABC, abstractmethod

from hermes.interface.assistant.prompt_builder.base import PromptBuilderFactory
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.message import AudioFileMessage, EmbeddedPDFMessage, ImageMessage, ImageUrlMessage, InvisibleMessage, Message, TextGeneratorMessage, TextMessage, TextualFileMessage, UrlMessage, VideoMessage
from hermes.utils.binary_file import is_binary

import logging

logger = logging.getLogger(__name__)

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
                content = message.get_content_for_assistant()
                if content:
                    content = content.strip()
                    if content:
                        self.handle_text_message(
                            text=content,
                            author=message.author,
                            message_id=id(message),
                            name=message.name,
                            text_role=message.text_role
                        )
            elif isinstance(message, TextGeneratorMessage):
                content = message.get_content_for_assistant()
                if content:
                    content = content.strip()
                    if content:
                        self.handle_text_message(content, message.author, id(message), message.name, message.text_role)
            elif isinstance(message, InvisibleMessage):
                content = message.get_content_for_assistant()
                if content:
                    content = content.strip()
                    if content:
                        self.handle_text_message(content, message.author, id(message), message.name, message.text_role)
            elif isinstance(message, ImageUrlMessage):
                content = message.get_content_for_assistant()
                if content:
                    self.handle_image_url_message(content, message.author, id(message))
            elif isinstance(message, ImageMessage):
                content = message.get_content_for_assistant()
                if content:
                    self.handle_image_message(content, message.author, id(message))
            elif isinstance(message, AudioFileMessage):
                content = message.get_content_for_assistant()
                if content:
                    self.handle_audio_file_message(content, message.author, id(message))
            elif isinstance(message, VideoMessage):
                content = message.get_content_for_assistant()
                if content:
                    self.handle_video_message(content, message.author, id(message))
            elif isinstance(message, EmbeddedPDFMessage):
                content = message.get_content_for_assistant()
                if content:
                    self.handle_embedded_pdf_message(content["pdf_filepath"], content["pages"], message.author, id(message))
            elif isinstance(message, TextualFileMessage):
                content = message.get_content_for_assistant()
                if content:
                    self.handle_textual_file_message(content, message.author, id(message))
            elif isinstance(message, UrlMessage):
                content = message.get_content_for_assistant()
                if content:
                    self.handle_url_message(content, message.author, id(message))
            else:
                self.notifications_printer.print_error(f"Unsupported message type: {type(message)}. Discarding message.")
                continue
        
        return self.compile_request()
    
    def handle_text_message(self, text: str, author: str, message_id: int, name: str = None, text_role: str = None):
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
            self.handle_text_message(markdown_content, author, message_id, name=url, text_role="webpage")
    
    def _get_url_text_content(self, url: str, message_id: int) -> str:
        if message_id in self._url_contents:
            return self._url_contents[message_id]
        try:
            from markitdown import MarkItDown
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            markitdown = MarkItDown()
            conversion_result = markitdown.convert(response)
            markdown_content = conversion_result.text_content
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

    def _default_handle_textual_file_message(self, text_filepath: str, author: str, message_id: int):
        """
        Read the content of the file, and create a text message with the content of the file
        Then use .handle_text_message with the filepath as name and 'textual_file' as role
        """
        from markitdown import MarkItDown, UnsupportedFormatException
        try:
            markitdown = MarkItDown()
            conversion_result = markitdown.convert(text_filepath)
            file_content = conversion_result.text_content
            self.handle_text_message(
                text=file_content,
                author=author,
                message_id=message_id,
                name=text_filepath,
                text_role="textual_file"
            )
        except UnsupportedFormatException as e:
            if not is_binary(text_filepath):
                logger.debug(f"Failed to use markitdown to get the data from {text_filepath}, reading it as a text file", e)
                with open(text_filepath) as f:
                    file_content = f.read()
                self.handle_text_message(
                    text=file_content,
                    author=author,
                    message_id=message_id,
                    name=text_filepath,
                    text_role="textual_file"
                )
            else:
                self.notifications_printer.print_error(f"Error reading file {text_filepath}: {e}")
                self.handle_text_message(f"Here was supposed to be the file content, but reading it failed: {text_filepath}: {e}", author, message_id, None, None)
        except Exception as e:
            self.notifications_printer.print_error(f"Error reading file {text_filepath}: {e}")
            self.handle_text_message(f"Here was supposed to be the file content, but reading it failed: {text_filepath}: {e}", author, message_id, None, None)

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
