import requests
from typing import Optional
from hermes.interface.assistant.request_builder.all_messages_aggregator import AllMessagesAggregator
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.text_messages_aggregator import TextMessagesAggregator


class BedrockRequestBuilder(RequestBuilder):
    def initialize_request(self):
        self.text_messages_aggregator = TextMessagesAggregator(self.prompt_builder_factory)
        self.all_messages_aggregator = AllMessagesAggregator()

    def _add_content(self, content: dict, author: str):
        self.all_messages_aggregator.add_message(content, author)
    
    def compile_request(self) -> any:
        self._flush_text_messages()

        final_messages = []
        for messages, author in self.all_messages_aggregator.get_aggregated_messages():
            final_messages.append({"role": self._get_message_role(author), "content": messages})

        # Using Converse API
        return {
            "modelId": self.model_tag,
            "system": [],
            "inferenceConfig": {},
            # "toolConfig": {},
            # "guardrailConfig": {},
            "messages": final_messages
        }
    
    def _flush_text_messages(self):
        content = self.text_messages_aggregator.compile_request()
        self._add_content({"text": content}, self.text_messages_aggregator.get_current_author())
        self.text_messages_aggregator.clear()
    
    def handle_text_message(self, text: str, author: str, message_id: int, name: str = None, text_role: str = None):
        if self.text_messages_aggregator.get_current_author() != author and not self.text_messages_aggregator.is_empty():
            self._flush_text_messages()
        self.text_messages_aggregator.add_message(message=text, author=author, message_id=message_id, name=name, text_role=text_role)
        
    def _get_message_role(self, role: str) -> str:
        if role == 'user':
            return "user"
        return "assistant"

    def handle_embedded_pdf_message(self, pdf_path: str, author: str, message_id: int):
        self._add_content({"document": {
                "format": "pdf",
                "name": self._get_file_name(pdf_path),
                "source": {
                    "bytes": self._get_file_bytes(pdf_path)
                }
            }}, author)
        
    def _get_file_name(self, file_path: str) -> str:
        import os
        return os.path.basename(file_path)

    def _get_file_bytes(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as file:
            return file.read()

    def handle_image_message(self, image_path: str, author: str, message_id: int):
        image_format = self._get_image_format(image_path)
        image_content = self._get_file_bytes(image_path)
        self._add_content({
            "image": {
                "format": image_format,
                "source": {
                    "bytes": image_content
                }
            }
        })
    
    def _get_image_format(self, image_path: str) -> str:
        import os
        _, file_extension = os.path.splitext(image_path)
        file_extension = file_extension[1:].lower()
        if file_extension in ['jpg', 'jpeg']:
            return 'jpeg'
        return file_extension

    def handle_image_url_message(self, url: str, author: str, message_id: int):
        image_content = requests.get(url).content
        self._add_content({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_content
            }
        }, author)

    def handle_textual_file_message(self, text_filepath: str, author: str, message_id: int, file_role: Optional[str] = None):
        return self._default_handle_textual_file_message(text_filepath, author, message_id, file_role)

    def handle_url_message(self, url: str, author: str, message_id: int):
        return self._default_handle_url_message(url, author, message_id)
