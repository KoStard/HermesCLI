from base64 import b64encode

from hermes.interface.assistant.models.request_builder.all_messages_aggregator import (
    AllMessagesAggregator,
)
from hermes.interface.assistant.models.request_builder.base import RequestBuilder
from hermes.interface.assistant.models.request_builder.text_messages_aggregator import (
    TextMessagesAggregator,
)
from hermes.utils.file_extension import get_file_extension


class ClaudeRequestBuilder(RequestBuilder):
    def initialize_request(self):
        self.text_messages_aggregator = TextMessagesAggregator(self.prompt_builder_factory)
        self.all_messages_aggregator = AllMessagesAggregator()
        self._extracted_pdfs = {}

    def _add_content(self, content: dict, author: str):
        self.all_messages_aggregator.add_message(content, author)

    def _flush_text_messages(self):
        content = self.text_messages_aggregator.compile_request()
        self._add_content(
            {"type": "text", "text": content},
            self.text_messages_aggregator.get_current_author(),
        )
        self.text_messages_aggregator.clear()

    def compile_request(self) -> any:
        self._flush_text_messages()

        final_messages = []
        for messages, author in self.all_messages_aggregator.get_aggregated_messages():
            final_messages.append({"role": self._get_message_role(author), "content": messages})

        return {
            "model": self.model_tag,
            "messages": final_messages,
            "max_tokens": 4096,
        }

    def handle_text_message(
        self,
        text: str,
        author: str,
        message_id: int,
        name: str = None,
        text_role: str = None,
    ):
        if self.text_messages_aggregator.get_current_author() != author and not self.text_messages_aggregator.is_empty():
            self._flush_text_messages()
        self.text_messages_aggregator.add_message(
            message=text,
            author=author,
            message_id=message_id,
            name=name,
            text_role=text_role,
        )

    def _get_message_role(self, role: str) -> str:
        if role == "user":
            return "user"
        return "assistant"

    def _get_base64(self, file_path: str) -> str:
        import base64

        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    def handle_embedded_pdf_message(self, pdf_path: str, pages: list[int], author: str, message_id: int):
        extracted_pdf_key = (pdf_path, tuple(pages))
        # Extract specified pages if pages are provided
        if extracted_pdf_key in self._extracted_pdfs:
            pdf_path = self._extracted_pdfs[extracted_pdf_key]
        else:
            if pages:
                pdf_path = self._extract_pages_from_pdf(pdf_path, pages)
            self._extracted_pdfs[extracted_pdf_key] = pdf_path

        self._add_content(
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": self._get_base64(pdf_path),
                },
            },
            author,
        )

    def _get_image_extension(self, image_path: str) -> str:
        return get_file_extension(image_path)

    def handle_image_message(self, image_path: str, author: str, message_id: int):
        self._add_content(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": f"image/{self._get_image_extension(image_path)}",
                    "data": self._get_base64(image_path),
                },
            },
            author,
        )

    def handle_image_url_message(self, url: str, author: str, message_id: int):
        image_data = self._get_url_image_content(url, message_id)
        base64_image = b64encode(image_data).decode("utf-8")
        self._add_content(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image,
                },
            },
            author,
        )

    def handle_textual_file_message(
        self,
        text_filepath: str,
        author: str,
        message_id: int,
        file_role: str | None = None,
    ):
        return self._default_handle_textual_file_message(text_filepath, author, message_id, file_role)

    def handle_url_message(self, url: str, author: str, message_id: int):
        return self._default_handle_url_message(url, author, message_id)
