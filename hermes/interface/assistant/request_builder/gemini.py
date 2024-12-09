from base64 import b64encode
import time
from hermes.interface.assistant.prompt_builder.base import PromptBuilderFactory
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.utils.file_extension import get_file_extension


class GeminiRequestBuilder(RequestBuilder):
    def __init__(self, model_tag: str, notifications_printer: CLINotificationsPrinter, prompt_builder_factory: PromptBuilderFactory):
        super().__init__(model_tag, notifications_printer, prompt_builder_factory)
        if model_tag.endswith("/grounded"):
            self.grounded = True
            self.model_tag = model_tag[:-len("/grounded")]
        else:
            self.grounded = False
        
        self.uploaded_files = {}
        self.extracted_pdfs = {}

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
    
    def _is_text_message(self, content: str | dict) -> bool:
        return isinstance(content, str)

    def _flush_active_author(self):
        if self._active_author:
            text_pieces = [content for content in self._active_author_contents if self._is_text_message(content)]
            joined_text = self._join_text_pieces(text_pieces)
            remaining_contents = [content for content in self._active_author_contents if not self._is_text_message(content)]
            self.messages.append({"role": self._get_message_role(self._active_author), "parts": [joined_text, *remaining_contents]})
            self._active_author = None
            self._active_author_contents = remaining_contents
    
    def handle_text_message(self, text: str, author: str, message_id: int):
        self._add_content(text, author)
    
    def compile_request(self) -> any:
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        self._wait_for_uploaded_files()
        self._flush_active_author()

        return {
            "model_kwargs": {
                "model_name": self.model_tag
            },
            "history": self._build_history(self.messages),
            "message": {
                "content": self.messages[-1]["parts"],
                "stream": True,
                "safety_settings": {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
                "tools": self._get_tools()
            }
        }
    
    def _get_tools(self):
        if self.grounded:
            return ["google_search_retrieval"]
        return None

    def _get_message_role(self, role):
        if role == 'user':
            return "user"
        return "model"
    
    def _build_history(self, messages: list[dict]):
        return messages[:-1]

    def handle_url_message(self, url: str, author: str, message_id: int):
        return self._default_handle_url_message(url, author, message_id)
    
    def handle_textual_file_message(self, text_filepath: str, author: str, message_id: int):
        return self._default_handle_textual_file_message(text_filepath, author, message_id)

    def handle_image_message(self, image_path: str, author: str, message_id: int):
        base64_image = self._get_base64_image(image_path)
        self._add_content({
            'mime_type': f'image/{self._get_extension(image_path)}',
            'data': base64_image
        }, author)

    def _get_base64_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode('utf-8')

    def _get_extension(self, image_path: str) -> str:
        return get_file_extension(image_path)
    
    def handle_image_url_message(self, url: str, author: str, message_id: int):
        image_data = self._get_url_image_content(url, message_id)
        base64_image = b64encode(image_data).decode('utf-8')
        self._add_content({
            'mime_type': 'image/jpeg',
            'data': base64_image
        }, author)

    def _get_file_hash(self, file_path: str):
        import hashlib
        return hashlib.md5(open(file_path, "rb").read()).hexdigest()
    
    def _upload_file(self, file_path: str):
        file_hash = self._get_file_hash(file_path)
        if file_path in self.uploaded_files:
            if self.uploaded_files[file_path]["hash"] == file_hash:
                return self.uploaded_files[file_path]["uploaded_file"]
        import google.generativeai as genai
        uploaded_file = genai.upload_file(path=file_path)
        self.uploaded_files[file_path] = {
            "uploaded_file": uploaded_file,
            "hash": file_hash
        }
        return uploaded_file
    
    def _get_uploaded_file_status(self, uploaded_file):
        import google.generativeai as genai
        recent_file = genai.get_file(uploaded_file.name)
        return recent_file.state.name
    
    def _wait_for_uploaded_files(self):
        for file_path, uploaded_file_details in self.uploaded_files.items():
            current_status = self._get_uploaded_file_status(uploaded_file_details["uploaded_file"])
            while current_status == 'PROCESSING':
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