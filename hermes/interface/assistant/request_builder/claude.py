from base64 import b64encode
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.utils.file_extension import get_file_extension


class ClaudeRequestBuilder(RequestBuilder):
    def initialize_request(self):
        self.messages = []

        self._active_author = None
        self._active_author_contents = []
        self._extracted_pdfs = {}

    def _add_content(self, content: str | dict, author: str):
        if self._active_author != author:
            self._flush_active_author()
            self._active_author = author
            self._active_author_contents = []
        self._active_author_contents.append(content)
    
    def _is_text_message(self, content: dict) -> bool:
        return isinstance(content, str)

    def _flush_active_author(self):
        if self._active_author:
            text_pieces = [content for content in self._active_author_contents if self._is_text_message(content)]
            joined_text = self._join_text_pieces(text_pieces)
            remaining_contents = [content for content in self._active_author_contents if not self._is_text_message(content)]
            self.messages.append({"role": self._get_message_role(self._active_author), "content": [joined_text, *remaining_contents]})
            self._active_author = None
            self._active_author_contents = remaining_contents
    
    def compile_request(self) -> any:
        self._flush_active_author()
        return {
            "model": self.model_tag,
            "messages": self.messages,
            "max_tokens": 4096,
        }
    
    def handle_text_message(self, text: str, author: str, message_id: int):
        self._add_content(text, author)
    
    def _get_message_role(self, role: str) -> str:
        if role == 'user':
            return "user"
        return "assistant"
    
    def _get_base64(self, file_path: str) -> str:
        import base64
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode('utf-8')

    def handle_embedded_pdf_message(self, pdf_path: str, pages: list[int], author: str, message_id: int):
        extracted_pdf_key = (pdf_path, tuple(pages))
        # Extract specified pages if pages are provided
        if extracted_pdf_key in self.extracted_pdfs:
            pdf_path = self.extracted_pdfs[extracted_pdf_key]
        else:
            if pages:
                pdf_path = self._extract_pages_from_pdf(pdf_path, pages)
            self.extracted_pdfs[extracted_pdf_key] = pdf_path
        self._add_content({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": self._get_base64(pdf_path)
            }
        }, author)

    def _get_image_extension(self, image_path: str) -> str:
        return get_file_extension(image_path)

    def handle_image_message(self, image_path: str, author: str, message_id: int):
        self._add_content({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": f"image/{self._get_image_extension(image_path)}",
                "data": self._get_base64(image_path)
            }
        }, author)

    def handle_image_url_message(self, url: str, author: str, message_id: int):
        image_data = self._get_url_image_content(url, message_id)
        base64_image = b64encode(image_data).decode('utf-8')
        self._add_content({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64_image
            }
        }, author)

    def handle_textual_file_message(self, text_filepath: str, author: str, message_id: int):
        return self._default_handle_textual_file_message(text_filepath, author, message_id)
    
    def handle_url_message(self, url: str, author: str, message_id: int):
        return self._default_handle_url_message(url, author, message_id)
