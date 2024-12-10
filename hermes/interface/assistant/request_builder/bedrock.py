import requests
from hermes.interface.assistant.request_builder.base import RequestBuilder


class BedrockRequestBuilder(RequestBuilder):
    def initialize_request(self):
        self.messages = []

        self._active_author = None
        self._active_author_contents = []

    def _add_content(self, content: dict, author: str):
        if self._active_author != author:
            self._flush_active_author()
            self._active_author = author
            self._active_author_contents = []
        self._active_author_contents.append(content)
    
    def _is_text_message(self, content: dict) -> bool:
        return "text" in content

    def _flush_active_author(self):
        if self._active_author:
            text_pieces = [content["text"] for content in self._active_author_contents if self._is_text_message(content)]
            joined_text = self._join_text_pieces(text_pieces)
            remaining_contents = [content for content in self._active_author_contents if not self._is_text_message(content)]
            self.messages.append({"role": self._get_message_role(self._active_author), "content": [{"text": joined_text}, *remaining_contents]})
            self._active_author = None
            self._active_author_contents = []
    
    def compile_request(self) -> any:
        # Using Converse API
        self._flush_active_author()
        return {
            "modelId": self.model_tag,
            "system": [],
            "inferenceConfig": {},
            # "toolConfig": {},
            # "guardrailConfig": {},
            "messages": self.messages
        }
    
    def handle_text_message(self, text: str, author: str, message_id: int):
        text = text.strip()
        if text:
            self._add_content({"text": text}, author)
        
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

    def handle_textual_file_message(self, text_filepath: str, author: str, message_id: int):
        return self._default_handle_textual_file_message(text_filepath, author, message_id)

    def handle_url_message(self, url: str, author: str, message_id: int):
        return self._default_handle_url_message(url, author, message_id)
