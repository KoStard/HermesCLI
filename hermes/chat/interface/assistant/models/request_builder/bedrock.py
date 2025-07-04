from typing import Any

from hermes.chat.interface.assistant.models.request_builder.all_messages_aggregator import (
    AllMessagesAggregator,
)
from hermes.chat.interface.assistant.models.request_builder.base import RequestBuilder
from hermes.chat.interface.assistant.models.request_builder.text_messages_aggregator import (
    TextMessagesAggregator,
)

MODEL_TAG_TO_MAX_TOKENS = {"claude-opus-4-20250514-v1": 32768, "claude-sonnet-4-20250514-v1": 64000, "claude-3-7": 124_000}


class BedrockRequestBuilder(RequestBuilder):
    def __init__(self, model_tag, notifications_printer, prompt_builder_factory):
        super().__init__(model_tag, notifications_printer, prompt_builder_factory)
        self.reasoning_effort: int | None = None

    def initialize_request(self):
        self.text_messages_aggregator = TextMessagesAggregator(self.prompt_builder_factory)
        self.all_messages_aggregator = AllMessagesAggregator()
        self._extracted_pdfs = {}

    def _add_content(self, content: dict, author: str):
        self.all_messages_aggregator.add_message(content, author)

    def _build_final_messages(self) -> list:
        """Build the final message list from aggregated messages."""
        final_messages = []
        for messages, author in self.all_messages_aggregator.get_aggregated_messages():
            final_messages.append({"role": self._get_message_role(author), "content": messages})
        return final_messages

    def _get_max_tokens_for_model(self) -> int | None:
        """Determine max tokens based on model tag."""
        for tag, tokens in MODEL_TAG_TO_MAX_TOKENS.items():
            if tag in self.model_tag:
                return tokens
        return None

    def _configure_inference_parameters(self, response: dict, max_tokens: int | None) -> None:
        """Configure inference parameters based on reasoning effort and max tokens."""
        if not self.reasoning_effort:
            return

        response["additionalModelRequestFields"] = {
            "thinking": {"type": "enabled", "budget_tokens": self.reasoning_effort},
        }

        if max_tokens:
            response["inferenceConfig"]["maxTokens"] = max_tokens
        else:
            response["inferenceConfig"]["maxTokens"] = self.reasoning_effort + 5000

    def compile_request(self) -> Any:
        """Compile the request for the Bedrock model."""
        self._flush_text_messages()

        final_messages = self._build_final_messages()
        response = {
            "modelId": self.model_tag,
            "system": [],
            "inferenceConfig": {},
            # "toolConfig": {},
            # "guardrailConfig": {},
            "messages": final_messages,
        }

        max_tokens = self._get_max_tokens_for_model()
        self._configure_inference_parameters(response, max_tokens)

        # Using Converse API
        return response

    def _flush_text_messages(self):
        content = self.text_messages_aggregator.compile_request()
        self._add_content({"text": content}, self.text_messages_aggregator.get_current_author())
        self.text_messages_aggregator.clear()

    def handle_text_message(
        self,
        text: str,
        author: str,
        message_id: int,
        name: str | None = None,
        text_role: str | None = None,
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

    def handle_embedded_pdf_message(self, pdf_path: str, pages: list[int], author: str, message_id: int):
        extracted_pdf_key = (pdf_path, tuple(pages))
        # Extract specified pages if pages are provided
        if extracted_pdf_key in self._extracted_pdfs:
            final_pdf_path = self._extracted_pdfs[extracted_pdf_key]
        else:
            final_pdf_path = self._extract_pages_from_pdf(pdf_path, pages) if pages else pdf_path
            self._extracted_pdfs[extracted_pdf_key] = final_pdf_path

        self._add_content(
            {
                "document": {
                    "format": "pdf",
                    "name": self._get_file_name(pdf_path),  # Using original name for PDF file
                    "source": {
                        "bytes": self._get_file_bytes(final_pdf_path),  # Using the extracted document
                    },
                },
            },
            author,
        )

    def _get_file_name(self, file_path: str) -> str:
        import os

        return os.path.basename(file_path)

    def _get_file_bytes(self, file_path: str) -> bytes:
        with open(file_path, "rb") as file:
            return file.read()

    def handle_image_message(self, image_path: str, author: str, message_id: int):
        image_format = self._get_image_format(image_path)
        image_content = self._get_file_bytes(image_path)
        self._add_content(
            {"image": {"format": image_format, "source": {"bytes": image_content}}},
            author,
        )

    def _get_image_format(self, image_path: str) -> str:
        import os

        _, file_extension = os.path.splitext(image_path)
        file_extension = file_extension[1:].lower()
        if file_extension in ["jpg", "jpeg"]:
            return "jpeg"
        return file_extension

    def handle_image_url_message(self, url: str, author: str, message_id: int):
        import requests

        image_content = requests.get(url).content
        self._add_content(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_content,
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

    def set_reasoning_effort(self, level: int | None):
        self.reasoning_effort = level
