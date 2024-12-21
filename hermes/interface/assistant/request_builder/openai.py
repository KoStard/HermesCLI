from base64 import b64encode
from typing import List, Dict, Any

from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.text_messages_aggregator import TextMessagesAggregator
from hermes.interface.assistant.request_builder.all_messages_aggregator import AllMessagesAggregator
from hermes.utils.file_extension import get_file_extension


class OpenAIRequestBuilder(RequestBuilder):
    def initialize_request(self):
        self.text_messages_aggregator = TextMessagesAggregator(self.prompt_builder_factory)
        self.all_messages_aggregator = AllMessagesAggregator()
        self.temperature = 0.7  # Default temperature

    def _add_content(self, content: dict, author: str):
        self.all_messages_aggregator.add_message(content, author)
    
    def _flush_text_messages(self):
        content = self.text_messages_aggregator.compile_request()
        self._add_content({
            "type": "text",
            "text": content
        }, self.text_messages_aggregator.get_current_author())
        self.text_messages_aggregator.clear()
        
    def handle_text_message(self, text: str, author: str, message_id: int, name: str = None, text_role: str = None):
        if self.text_messages_aggregator.get_current_author() != author and not self.text_messages_aggregator.is_empty():
            self._flush_text_messages()
        self.text_messages_aggregator.add_message(message=text, author=author, message_id=message_id, name=name, text_role=text_role)
    
    def handle_image_message(self, image_path: str, author: str, message_id: int):
        base64_image = self._get_base64_image(image_path)
        
        self._add_content({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{self._get_extension(image_path)};base64,{base64_image}"
            }
        }, author)
    
    def _get_base64_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode('utf-8')
    
    def _get_extension(self, image_path: str) -> str:
        return get_file_extension(image_path)
    
    def handle_image_url_message(self, url: str, author: str, message_id: int):
        self._add_content({
            "type": "image_url",
            "image_url": {
                "url": url
            }
        }, author)

    def handle_textual_file_message(self, text_filepath: str, author: str, message_id: int):
        self._default_handle_textual_file_message(text_filepath, author, message_id)

    def handle_url_message(self, url: str, author: str, message_id: int):
        self._default_handle_url_message(url, author, message_id)

    def compile_request(self) -> dict:
        self._flush_text_messages()

        final_messages = []
        for messages, author in self.all_messages_aggregator.get_aggregated_messages():
            final_messages.append({
                "role": author,
                "content": messages if len(messages) > 1 else messages[0]["text"]
            })

        return {
            "model": self.model_tag,
            "messages": final_messages,
            "stream": True,
            "temperature": self.temperature,
        }
