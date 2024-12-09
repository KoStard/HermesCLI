from hermes.interface.assistant.request_builder.base import RequestBuilder


class BedrockRequestBuilder(RequestBuilder):
    def initialize_request(self):
        self.messages = []

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
            self.messages.append({"role": self._get_message_role(self._active_author), "content": self._active_author_contents})
            self._active_author = None
            self._active_author_contents = []
    
    def compile_request(self) -> any:
        # Using Converse API
        self._flush_active_author()
        return {
            "modelId": self.model_tag,
            "system": [],
            "inferenceConfig": {},
            "toolConfig": {},
            "guardrailConfig": {},
            "messages": self.messages
        }
    
    def handle_text_message(self, text: str, author: str):
        self._add_content(text, author)
        
    def _get_message_role(self, role: str) -> str:
        if role == 'user':
            return "user"
        return "assistant"

    def handle_embedded_pdf_message(self, pdf_path: str, author: str):
        # Only for anthropic models
        pass

    def handle_image_message(self, image_path: str, author: str):
        pass

    def handle_image_url_message(self, url: str, author: str):
        pass

    def handle_textual_file_message(self, text_filepath: str, author: str):
        return self._default_handle_textual_file_message(text_filepath, author)

    def handle_url_message(self, url: str, author: str):
        return self._default_handle_url_message(url, author)
