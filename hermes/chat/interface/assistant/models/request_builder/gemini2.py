import typing
from base64 import b64encode

from hermes.chat.interface.assistant.models.prompt_builder.base import PromptBuilderFactory
from hermes.chat.interface.assistant.models.request_builder.all_messages_aggregator import (
    AllMessagesAggregator,
)
from hermes.chat.interface.assistant.models.request_builder.base import RequestBuilder
from hermes.chat.interface.assistant.models.request_builder.text_messages_aggregator import (
    TextMessagesAggregator,
)
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.utils.file_extension import get_file_extension

if typing.TYPE_CHECKING:
    from google.genai import Client


class Gemini2RequestBuilder(RequestBuilder):
    def __init__(
        self,
        model_tag: str,
        notifications_printer: CLINotificationsPrinter,
        prompt_builder_factory: PromptBuilderFactory,
        google_client: "Client",
    ):
        super().__init__(model_tag, notifications_printer, prompt_builder_factory)
        from google.genai.types import GoogleSearch, Tool

        if model_tag.endswith("/grounded"):
            self.grounded = True
            self.model_tag = model_tag[: -len("/grounded")]
        else:
            self.grounded = False

        self.uploaded_files = {}
        self.extracted_pdfs = {}
        self.google_search_tool = Tool(google_search=GoogleSearch())
        self.google_client = google_client

    def initialize_request(self):
        self.text_messages_aggregator = TextMessagesAggregator(self.prompt_builder_factory)
        self.all_messages_aggregator = AllMessagesAggregator()

    def _add_part(self, content: str | dict, author: str):
        self.all_messages_aggregator.add_message(content, author)

    def _flush_text_messages(self):
        from google.genai.types import Part

        content = self.text_messages_aggregator.compile_request()
        part = Part.from_text(text=content)
        self._add_part(part, self.text_messages_aggregator.get_current_author())
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

    def compile_request(self) -> typing.Any:
        from google.genai.types import Content

        # self._wait_for_uploaded_files()
        self._flush_text_messages()

        final_messages = []
        for parts, author in self.all_messages_aggregator.get_aggregated_messages():
            role = "user" if author == "user" else "model"
            final_messages.append(Content(role=role, parts=parts))

        tools = []
        if self.grounded:
            tools.append(self.google_search_tool)

        return {
            "model_name": self.model_tag,
            "contents": final_messages,
            "tools": tools,
            "config": {"response_modalities": ["TEXT"]},
        }

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
        from google.genai.types import Part

        uploaded_file = self._upload_file(image_path)
        uploaded_file = Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
        self._add_part(uploaded_file, author)

    def _get_base64_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode("utf-8")

    def _get_extension(self, image_path: str) -> str:
        return get_file_extension(image_path)

    def handle_image_url_message(self, url: str, author: str, message_id: int):
        image_data = self._get_url_image_content(url, message_id)
        base64_image = b64encode(image_data).decode("utf-8")
        self._add_part({"mime_type": "image/jpeg", "data": base64_image}, author)

    def _get_file_hash(self, file_path: str):
        import hashlib

        return hashlib.md5(open(file_path, "rb").read()).hexdigest()

    def _upload_file(self, file_path: str):
        file_hash = self._get_file_hash(file_path)
        if file_path in self.uploaded_files and self.uploaded_files[file_path]["hash"] == file_hash:
            return self.uploaded_files[file_path]["uploaded_file"]

        uploaded_file = self.google_client.files.upload(path=file_path)
        self.uploaded_files[file_path] = {
            "uploaded_file": uploaded_file,
            "hash": file_hash,
        }
        return uploaded_file

    # def _get_uploaded_file_status(self, uploaded_file):
    #     recent_file = self.google_client.files.get(name=uploaded_file.name)
    #     return recent_file.state

    # def _wait_for_uploaded_files(self):
    #     for file_path, uploaded_file_details in self.uploaded_files.items():
    #         current_status = self._get_uploaded_file_status(uploaded_file_details["uploaded_file"])
    #         while current_status == 'PROCESSING':
    #             self.notifications_printer.print_info(f"Waiting for file {file_path} to be processed...")
    #             time.sleep(0.5)
    #             current_status = self._get_uploaded_file_status(uploaded_file_details["uploaded_file"])
    #         print(f"File {file_path} processed, status: {current_status}")

    def handle_audio_file_message(self, audio_path: str, author: str, message_id: int):
        from google.genai.types import Part

        uploaded_file = self._upload_file(audio_path)
        uploaded_file = Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
        self._add_part(uploaded_file, author)

    def handle_video_message(self, video_path: str, author: str, message_id: int):
        from google.genai.types import Part

        uploaded_file = self._upload_file(video_path)
        uploaded_file = Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
        self._add_part(uploaded_file, author)

    def handle_embedded_pdf_message(self, pdf_path: str, pages: list[int], author: str, message_id: int):
        from google.genai.types import Part

        extracted_pdf_key = (pdf_path, tuple(pages))
        if extracted_pdf_key in self.extracted_pdfs:
            pdf_path = self.extracted_pdfs[extracted_pdf_key]
        else:
            # Extract specified pages if pages are provided
            if pages:
                pdf_path = self._extract_pages_from_pdf(pdf_path, pages)
            self.extracted_pdfs[extracted_pdf_key] = pdf_path

        uploaded_file = self._upload_file(pdf_path)
        uploaded_file = Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
        self._add_part(uploaded_file, author)
