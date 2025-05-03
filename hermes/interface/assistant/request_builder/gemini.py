import time
from base64 import b64encode

from hermes.interface.assistant.prompt_builder.base import PromptBuilderFactory
from hermes.interface.assistant.request_builder.all_messages_aggregator import (
    AllMessagesAggregator,
)
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.text_messages_aggregator import (
    TextMessagesAggregator,
)
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.utils.file_extension import get_file_extension


class GeminiRequestBuilder(RequestBuilder):
    def __init__(
        self,
        model_tag: str,
        notifications_printer: CLINotificationsPrinter,
        prompt_builder_factory: PromptBuilderFactory,
    ):
        super().__init__(model_tag, notifications_printer, prompt_builder_factory)
        if model_tag.endswith("/grounded"):
            self.grounded = True
            self.model_tag = model_tag[: -len("/grounded")]
        else:
            self.grounded = False

        self.uploaded_files = {}
        self.extracted_pdfs = {}

    def initialize_request(self):
        self.text_messages_aggregator = TextMessagesAggregator(self.prompt_builder_factory)
        self.all_messages_aggregator = AllMessagesAggregator()

    def _add_content(self, content: str | dict, author: str):
        self.all_messages_aggregator.add_message(content, author)

    def _flush_text_messages(self):
        content = self.text_messages_aggregator.compile_request()
        self._add_content(content, self.text_messages_aggregator.get_current_author())
        self.text_messages_aggregator.clear()

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

    def compile_request(self) -> any:
        from google.generativeai.types import HarmBlockThreshold, HarmCategory

        self._wait_for_uploaded_files()
        self._flush_text_messages()

        final_messages = []
        for messages, author in self.all_messages_aggregator.get_aggregated_messages():
            final_messages.append({"role": self._get_message_role(author), "parts": messages})

        return {
            "model_kwargs": {"model_name": self.model_tag},
            "history": self._build_history(final_messages),
            "message": {
                "content": final_messages[-1]["parts"],
                "stream": True,
                "safety_settings": {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
                "tools": self._get_tools(),
            },
        }

    def _get_tools(self):
        if self.grounded:
            return ["google_search_retrieval"]
        return None

    def _get_message_role(self, role):
        if role == "user":
            return "user"
        return "model"

    def _build_history(self, messages: list[dict]):
        return messages[:-1]

    def handle_url_message(self, url: str, author: str, message_id: int):
        return self._default_handle_url_message(url, author, message_id)

    def handle_textual_file_message(
        self,
        text_filepath: str,
        author: str,
        message_id: int,
        file_role: str | None = None,
    ):
        return self._default_handle_textual_file_message(text_filepath, author, message_id, file_role)

    def handle_image_message(self, image_path: str, author: str, message_id: int):
        uploaded_file = self._upload_file(image_path)
        self._add_content(uploaded_file, author)

    def _get_base64_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode("utf-8")

    def _get_extension(self, image_path: str) -> str:
        return get_file_extension(image_path)

    def handle_image_url_message(self, url: str, author: str, message_id: int):
        image_data = self._get_url_image_content(url, message_id)
        base64_image = b64encode(image_data).decode("utf-8")
        self._add_content({"mime_type": "image/jpeg", "data": base64_image}, author)

    def _get_file_hash(self, file_path: str):
        import hashlib

        return hashlib.md5(open(file_path, "rb").read()).hexdigest()

    def _upload_file(self, file_path: str):
        file_hash = self._get_file_hash(file_path)
        if file_path in self.uploaded_files and self.uploaded_files[file_path]["hash"] == file_hash:
            return self.uploaded_files[file_path]["uploaded_file"]
        import google.generativeai as genai

        uploaded_file = genai.upload_file(path=file_path)
        self.uploaded_files[file_path] = {
            "uploaded_file": uploaded_file,
            "hash": file_hash,
        }
        return uploaded_file

    def _get_uploaded_file_status(self, uploaded_file):
        import google.generativeai as genai

        recent_file = genai.get_file(uploaded_file.name)
        return recent_file.state.name

    def _wait_for_uploaded_files(self):
        for file_path, uploaded_file_details in self.uploaded_files.items():
            current_status = self._get_uploaded_file_status(uploaded_file_details["uploaded_file"])
            while current_status == "PROCESSING":
                self.notifications_printer.print_info(f"Waiting for file {file_path} to be processed...")
                time.sleep(0.5)
                current_status = self._get_uploaded_file_status(uploaded_file_details["uploaded_file"])
            print(f"File {file_path} processed, status: {current_status}")

    def handle_audio_file_message(self, audio_path: str, author: str, message_id: int):
        uploaded_file = self._upload_file(audio_path)
        self._add_content(uploaded_file, author)

    def handle_video_message(self, video_path: str, author: str, message_id: int):
        uploaded_file = self._upload_file(video_path)
        self._add_content(uploaded_file, author)

    def handle_embedded_pdf_message(self, pdf_path: str, pages: list[int], author: str, message_id: int):
        extracted_pdf_key = (pdf_path, tuple(pages))
        if extracted_pdf_key in self.extracted_pdfs:
            pdf_path = self.extracted_pdfs[extracted_pdf_key]
        else:
            # Extract specified pages if pages are provided
            if pages:
                pdf_path = self._extract_pages_from_pdf(pdf_path, pages)
            self.extracted_pdfs[extracted_pdf_key] = pdf_path

        uploaded_file = self._upload_file(pdf_path)
        self._add_content(uploaded_file, author)
