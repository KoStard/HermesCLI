"""
Messages are what the participant sends to the other participant through the engine
Some messages are commands, they might not go through to the other participant, maybe they are for the engine itself.
Imagine using Telegram or some other messaging app. What you can add and press Send is what a message is. With difference that you can send multiple messages at once.
"""



import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, Optional
from abc import ABC, abstractmethod

import requests

from hermes_beta.utils.binary_file import is_binary
from hermes_beta.utils.file_extension import get_file_extension

@dataclass(init=False)
class Message(ABC):
    """
    Base abstract class for all message types
    A single message might represent only a part of the message
    During one interaction, a single participant might send multiple messages
    """
    author: str
    timestamp: datetime
    
    def __init__(self, *, author: str, timestamp: Optional[datetime] = None):
        self.author = author
        self.timestamp = timestamp or datetime.now()
    
    @abstractmethod
    def get_content_for_user(self) -> str:
        pass

    @abstractmethod
    def get_content_for_assistant(self) -> dict:
        pass

    @abstractmethod
    def to_json(self) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def from_json(json_data: dict) -> "Message":
        pass

@dataclass(init=False)
class TextMessage(Message):
    """Class for regular text messages"""
    
    text: str
    
    def __init__(self, *, author: str, text: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.text = text
    
    def get_content_for_user(self) -> str:
        return self.text

    def get_content_for_assistant(self) -> dict:
        return self.text
    
    def to_json(self) -> dict:
        return {
            "type": "text",
            "text": self.text,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }
    
    @staticmethod
    def from_json(json_data: dict) -> "TextMessage":
        return TextMessage(author=json_data["author"], text=json_data["text"], timestamp=datetime.fromisoformat(json_data["timestamp"]))

@dataclass(init=False)
class TextGeneratorMessage(Message):
    """Class for messages that contain a text generator"""
    
    text_generator: Generator[str, None, None]
    text: str
    has_finished: bool

    def __init__(self, *, author: str, text_generator: Generator[str, None, None], timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        # We should track the output of the generator, and save it to self.text
        self.text_generator = text_generator
        self.text = ""
        self.has_finished = False

    def get_content_for_user(self) -> Generator[str, None, None]:
        # Yield each new chunk from the generator and accumulate in self.text
        if self.text:
            yield self.text
        if not self.has_finished:
            for chunk in self.text_generator:
                self.text += chunk
                yield chunk
            self.has_finished = True

    def get_content_for_assistant(self):
        for chunk in self.text_generator:
            self.text += chunk

        return self.text

    def to_json(self) -> dict:
        return {
            "type": "text_generator",
            "text": self.text,
            "has_finished": self.has_finished,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "TextGeneratorMessage":
        # Since we can't serialize a generator, we'll create a simple generator that yields the stored text
        def text_gen():
            yield json_data["text"]
        
        msg = TextGeneratorMessage(
            author=json_data["author"],
            text_generator=text_gen(),
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )
        msg.text = json_data["text"]
        msg.has_finished = json_data["has_finished"]
        return msg

@dataclass(init=False)
class InvisibleMessage(TextMessage):
    """Class for messages that are invisible to the user"""
    
    def get_content_for_user(self) -> str:
        return ""

@dataclass(init=False)
class AutoRedactedInvisibleTextMessage(InvisibleMessage):
    """Class for messages that are automatically redacted from the LLM and are invisible to the user"""
    text: str
    redacted_text: str

    def __init__(self, *, author: str, text: str, redacted_text: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.text = text
        self.redacted_text = redacted_text
        self.is_redacted = False
    
    def get_content_for_user(self) -> str:
        return ""

    def get_content_for_assistant(self) -> str:
        if not self.is_redacted:
            self.is_redacted = True
            return self.text
        return self.redacted_text

    def to_json(self) -> dict:
        return {
            "type": "auto_redacted_invisible",
            "text": self.text,
            "redacted_text": self.redacted_text,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "is_redacted": self.is_redacted
        }

    @staticmethod
    def from_json(json_data: dict) -> "AutoRedactedInvisibleTextMessage":
        msg = AutoRedactedInvisibleTextMessage(
            author=json_data["author"],
            text=json_data["text"],
            redacted_text=json_data["redacted_text"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )
        msg.is_redacted = json_data["is_redacted"]
        return msg


@dataclass(init=False)
class ImageUrlMessage(Message):
    """Class for messages that are image urls"""
    image_url: str

    def __init__(self, *, author: str, image_url: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.image_url = image_url

    def get_content_for_user(self) -> str:
        return f"Image URL: {self.image_url}"

    def get_content_for_assistant(self) -> dict:
        return self.image_url
    
    def to_json(self) -> dict:
        return {
            "type": "image_url",
            "image_url": self.image_url,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "ImageUrlMessage":
        return ImageUrlMessage(
            author=json_data["author"],
            image_url=json_data["image_url"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )

@dataclass(init=False)
class ImageMessage(Message):
    """Class for messages that are images"""
    image_path: str

    IMAGE_EXTENSION_MAP = {
        "jpg": "jpeg",
    }

    def __init__(self, *, author: str, image_path: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.image_path = image_path
    
    # def _encode_image(self, image_path: str) -> str:
    #     with open(image_path, "rb") as image_file:
    #         return base64.b64encode(image_file.read()).decode("utf-8")
    
    # def _get_extension(self, image_path: str) -> str:
    #     extension = get_file_extension(image_path)
    #     return self.IMAGE_EXTENSION_MAP.get(extension, extension)

    def get_content_for_user(self) -> str:
        return f"Image: {self.image_path}"
    
    def get_content_for_assistant(self):
        return self.image_path

    # def get_content_for_assistant(self) -> dict:
    #     return {
    #         "type": "image_url",
    #         "image_url": {
    #             "url": f"data:image/{self._get_extension(self.image_path)};base64,{self._encode_image(self.image_path)}"
    #         }
    #     }

    def to_json(self) -> dict:
        return {
            "type": "image",
            "image_path": self.image_path,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "ImageMessage":
        return ImageMessage(
            author=json_data["author"],
            image_path=json_data["image_path"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )


@dataclass(init=False)
class AudioFileMessage(Message):
    """Class for messages that are audio files"""
    audio_filepath: str

    def __init__(self, *, author: str, audio_filepath: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.audio_filepath = audio_filepath

    # def _encode_audio(self, audio_filepath: str) -> str:
    #     with open(audio_filepath, "rb") as audio_file:
    #         return base64.b64encode(audio_file.read()).decode("utf-8")
    
    def get_content_for_user(self) -> str:
        return f"Audio: {self.audio_filepath}"
    
    def get_content_for_assistant(self):
        return self.audio_filepath

    # def get_content_for_assistant(self) -> dict:
    #     return {
    #         "type": "image_url",
    #         "image_url": {
    #             "url": f"data:audio/{get_file_extension(self.audio_filepath)};base64,{self._encode_audio(self.audio_filepath)}"
    #         }
    #     }

    def to_json(self) -> dict:
        return {
            "type": "audio",
            "audio_filepath": self.audio_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "AudioFileMessage":
        return AudioFileMessage(
            author=json_data["author"],
            audio_filepath=json_data["audio_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )

@dataclass(init=False)
class VideoMessage(Message):
    """Class for messages that are videos"""
    video_filepath: str

    def __init__(self, *, author: str, video_filepath: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.video_filepath = video_filepath

    def get_content_for_user(self) -> str:
        return f"Video: {self.video_filepath}"
    
    # def _encode_video(self, video_filepath: str) -> str:
    #     with open(video_filepath, "rb") as video_file:
    #         return base64.b64encode(video_file.read()).decode("utf-8")
        
    def get_content_for_assistant(self):
        return self.video_filepath
    
    # # def get_content_for_assistant(self) -> dict:
    #     return {
    #         "type": "image_url",
    #         "image_url": f"data:video/{get_file_extension(self.video_filepath)};base64,{self._encode_video(self.video_filepath)}"
    #     }

    def to_json(self) -> dict:
        return {
            "type": "video",
            "video_filepath": self.video_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "VideoMessage":
        return VideoMessage(
            author=json_data["author"],
            video_filepath=json_data["video_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )


@dataclass(init=False)
class EmbeddedPDFMessage(Message):
    """Class for messages that are embedded PDFs"""
    pdf_filepath: str

    def __init__(self, *, author: str, pdf_filepath: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.pdf_filepath = pdf_filepath

    def get_content_for_user(self) -> str:
        return f"PDF: {self.pdf_filepath}"

    # def get_content_for_assistant(self) -> dict:
    #     with open(self.pdf_filepath, "rb") as pdf_file:
    #         encoded_file = base64.b64encode(pdf_file.read()).decode("utf-8")
    #     return {
    #         "type": "image_url",
    #         "image_url": f"data:application/pdf;base64,{encoded_file}",
    #     }

    def get_content_for_assistant(self):
        return self.pdf_filepath

    def to_json(self) -> dict:
        return {
            "type": "pdf",
            "pdf_filepath": self.pdf_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "EmbeddedPDFMessage":
        return EmbeddedPDFMessage(
            author=json_data["author"],
            pdf_filepath=json_data["pdf_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )

@dataclass(init=False)
class TextualFileMessage(Message):
    """Class for messages that are textual files"""
    text_filepath: str

    def __init__(self, *, author: str, text_filepath: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.text_filepath = text_filepath

    def get_content_for_user(self) -> str:
        return f"Text file: {self.text_filepath}"
    
    # def _get_file_content(self, filepath: str) -> str:
    #     if is_binary(filepath):
    #         extension = get_file_extension(filepath)
    #         if extension == "pdf":
    #             return self._extract_text_from_pdf(filepath)
    #         elif extension == "docx":
    #             return self._extract_text_from_docx(filepath)
    #         else:
    #             raise ValueError(f"File {filepath} is binary, cannot be converted to text")
    #     with open(filepath, "r") as file:
    #         return file.read()

    def get_content_for_assistant(self):
        return self.text_filepath

    # def _extract_text_from_pdf(self, file_path: str) -> str:
    #     import PyPDF2
    #     with open(file_path, 'rb') as file:
    #         reader = PyPDF2.PdfReader(file)
    #         return ' '.join(page.extract_text() for page in reader.pages)

    # def _extract_text_from_docx(self, file_path: str) -> str:
    #     import docx
    #     doc = docx.Document(file_path)
    #     return ' '.join(paragraph.text for paragraph in doc.paragraphs)

    def to_json(self) -> dict:
        return {
            "type": "textual_file",
            "text_filepath": self.text_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "TextualFileMessage":
        return TextualFileMessage(
            author=json_data["author"],
            text_filepath=json_data["text_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )

@dataclass(init=False)
class UrlMessage(Message):
    """Class for messages that are urls"""
    url: str

    def __init__(self, *, author: str, url: str, timestamp: Optional[datetime] = None):
        super().__init__(author=author, timestamp=timestamp)
        self.url = url  
    
    def get_content_for_user(self) -> str:
        return f"URL: {self.url}"
    
    def _get_url_content(self, url: str) -> str:
        response = requests.get(url)
        return response.text
    
    def _convert_html_to_markdown(self, html: str) -> str:
        """
        Converts HTML content to Markdown format.

        Args:
            html (str): The HTML content to convert.

        Returns:
            str: The converted Markdown content.
        """
        from markdownify import markdownify as md
        try:
            markdown = md(html)
            return markdown
        except Exception as e:
            # Handle or log the exception as needed
            print(f"Error converting HTML to Markdown, falling back to raw HTML: {e}")
            return html

    def get_content_for_assistant(self):
        return self.url
        # html_content = self._get_url_content(self.url)
        # markdown_content = self._convert_html_to_markdown(html_content)
        # return {
        #     "type": "text",
        #     "text": markdown_content
        # }

    def to_json(self) -> dict:
        return {
            "type": "url",
            "url": self.url,
            "author": self.author,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def from_json(json_data: dict) -> "UrlMessage":
        return UrlMessage(
            author=json_data["author"],
            url=json_data["url"],
            timestamp=datetime.fromisoformat(json_data["timestamp"])
        )



DESERIALIZATION_KEYMAP = {
    "text": TextMessage.from_json,
    "text_generator": TextGeneratorMessage.from_json,
    "invisible": InvisibleMessage.from_json,
    "auto_redacted_invisible": AutoRedactedInvisibleTextMessage.from_json,
    "image_url": ImageUrlMessage.from_json,
    "image": ImageMessage.from_json,
    "audio": AudioFileMessage.from_json,
    "video": VideoMessage.from_json,
    "pdf": EmbeddedPDFMessage.from_json,
    "textual_file": TextualFileMessage.from_json,
    "url": UrlMessage.from_json,
}