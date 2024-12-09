from base64 import b64encode
from typing import List, Dict, Any

from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.utils.file_extension import get_file_extension


class OpenAIRequestBuilder(RequestBuilder):
    def initialize_request(self):
        self.messages: List[Dict[str, Any]] = []
        self.max_tokens = 4096  # Default max tokens
        self.temperature = 0.7  # Default temperature

        self._active_author = None
        self._active_author_contents = []

    def _add_content(self, content: str | dict, author: str):
        if self._active_author != author:
            self._flush_active_author()
            self._active_author = author
            self._active_author_contents = []
        self._active_author_contents.append(content)

    def _flush_active_author(self):
        if self._active_author:
            self.messages.append({"role": self._active_author, "content": self._active_author_contents})
            self._active_author = None
            self._active_author_contents = []
        
    def handle_text_message(self, text: str, author: str):
        self._add_content({
            "type": "text",
            "text": text
        }, author)
    
    def handle_image_message(self, image_path: str, author: str):
        base64_image = self._get_base64_image(image_path)
        
        # Create content list with text and image
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{self._get_extension(image_path)};base64,{base64_image}"
                }
            }
        ]
        
        self._add_content(content, author)
    
    def _get_base64_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode('utf-8')
    
    def _get_extension(self, image_path: str) -> str:
        return get_file_extension(image_path)
    
    def handle_image_url_message(self, url: str, author: str):
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": url
                }
            }
        ]
        
        self._add_content(content, author)

    def handle_textual_file_message(self, text_filepath: str, author: str):
        self._default_handle_url_message(text_filepath, author)

    def handle_url_message(self, url: str, author: str):
        self._default_handle_url_message(url, author)


    def compile_request(self) -> dict:
        self._flush_active_author()
        return {
            "model": self.model_tag,
            "messages": self.messages,
            "stream": True,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
