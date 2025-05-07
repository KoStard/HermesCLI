"""
Messages are what the participant sends to the other participant through the engine
Some messages are commands, they might not go through to the other participant, maybe they are for the engine itself.
Imagine using Telegram or some other messaging app. What you can add and press Send is what a message is.
With difference that you can send multiple messages at once.
"""

import os
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime

from hermes.interface.assistant.chat_assistant.response_types import (
    BaseLLMResponse,
    ThinkingLLMResponse,
)
from hermes.interface.helpers.chunks_to_lines import chunks_to_lines
from hermes.interface.helpers.peekable_generator import PeekableGenerator, iterate_while
from hermes.utils.file_extension import remove_quotes
from hermes.utils.filepath import prepare_filepath


@dataclass(init=False)
class Message(ABC):
    """
    Base abstract class for all message types
    A single message might represent only a part of the message
    During one interaction, a single participant might send multiple messages
    """

    author: str
    timestamp: datetime

    def __init__(self, *, author: str, timestamp: datetime | None = None):
        self.author = author
        self.timestamp = timestamp or datetime.now()

    @abstractmethod
    def get_content_for_user(self) -> str:
        pass

    @abstractmethod
    def get_content_for_assistant(self) -> any:
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
    is_directly_entered: bool
    name: str | None
    text_role: str | None

    def __init__(
        self,
        *,
        author: str,
        text: str,
        timestamp: datetime | None = None,
        is_directly_entered: bool = False,
        name: str | None = None,
        text_role: str | None = None,
    ):
        super().__init__(author=author, timestamp=timestamp)
        self.text = text
        self.is_directly_entered = is_directly_entered
        self.name = name
        self.text_role = text_role

    def get_content_for_user(self) -> str:
        return self.text

    def get_content_for_assistant(self) -> str:
        return self.text

    def to_json(self) -> dict:
        return {
            "type": "text",
            "text": self.text,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "is_directly_entered": self.is_directly_entered,
            "name": self.name,
            "text_role": self.text_role,
        }

    @staticmethod
    def from_json(json_data: dict) -> "TextMessage":
        return TextMessage(
            author=json_data["author"],
            text=json_data["text"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            is_directly_entered=json_data["is_directly_entered"],
            name=json_data.get("name"),
            text_role=json_data.get("text_role"),
        )


@dataclass(init=False)
class TextGeneratorMessage(Message):
    """Class for messages that contain a text generator"""

    text_generator: Generator[str, None, None]
    text: str
    has_finished: bool
    is_directly_entered: bool
    name: str | None
    text_role: str | None

    def __init__(
        self,
        *,
        author: str,
        text_generator: Generator[str, None, None],
        timestamp: datetime | None = None,
        is_directly_entered: bool = False,
        name: str | None = None,
        text_role: str | None = None,
    ):
        super().__init__(author=author, timestamp=timestamp)
        # We should track the output of the generator, and save it to self.text
        self.text_generator = text_generator
        self.text = ""
        self.has_finished = False
        self.is_directly_entered = is_directly_entered
        self.name = name
        self.text_role = text_role

    def get_content_for_user(self) -> Generator[str, None, None]:
        # Yield each new chunk from the generator and accumulate in self.text
        if self.text:
            yield self.text
        if not self.has_finished:
            for chunk in self.text_generator:
                self.text += chunk
                yield chunk
            self.has_finished = True

    def get_content_for_assistant(self) -> str:
        for chunk in self.text_generator:
            self.text += chunk

        return self.text

    def to_json(self) -> dict:
        return {
            "type": "text_generator",
            "text": self.text,
            "has_finished": self.has_finished,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "is_directly_entered": self.is_directly_entered,
            "name": self.name,
            "text_role": self.text_role,
        }

    @staticmethod
    def from_json(json_data: dict) -> "TextGeneratorMessage":
        # Since we can't serialize a generator, we'll create a simple generator that yields the stored text
        def text_gen():
            yield json_data["text"]

        msg = TextGeneratorMessage(
            author=json_data["author"],
            text_generator=text_gen(),
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            is_directly_entered=json_data.get("is_directly_entered", False),
            name=json_data.get("name"),
            text_role=json_data.get("text_role"),
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
class ImageUrlMessage(Message):
    """Class for messages that are image urls"""

    image_url: str

    def __init__(self, *, author: str, image_url: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.image_url = image_url

    def get_content_for_user(self) -> str:
        return f"Image URL: {self.image_url}"

    def get_content_for_assistant(self) -> str:
        return self.image_url

    def to_json(self) -> dict:
        return {
            "type": "image_url",
            "image_url": self.image_url,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "ImageUrlMessage":
        return ImageUrlMessage(
            author=json_data["author"],
            image_url=json_data["image_url"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class ImageMessage(Message):
    """Class for messages that are images"""

    image_path: str

    IMAGE_EXTENSION_MAP = {
        "jpg": "jpeg",
    }

    def __init__(self, *, author: str, image_path: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.image_path = prepare_filepath(image_path)

    def get_content_for_user(self) -> str:
        return f"Image: {self.image_path}"

    def get_content_for_assistant(self) -> str:
        return self.image_path

    def to_json(self) -> dict:
        return {
            "type": "image",
            "image_path": self.image_path,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "ImageMessage":
        return ImageMessage(
            author=json_data["author"],
            image_path=json_data["image_path"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class AudioFileMessage(Message):
    """Class for messages that are audio files"""

    audio_filepath: str

    def __init__(self, *, author: str, audio_filepath: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.audio_filepath = prepare_filepath(audio_filepath)

    def get_content_for_user(self) -> str:
        return f"Audio: {self.audio_filepath}"

    def get_content_for_assistant(self) -> str:
        return self.audio_filepath

    def to_json(self) -> dict:
        return {
            "type": "audio",
            "audio_filepath": self.audio_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "AudioFileMessage":
        return AudioFileMessage(
            author=json_data["author"],
            audio_filepath=json_data["audio_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class VideoMessage(Message):
    """Class for messages that are videos"""

    video_filepath: str

    def __init__(self, *, author: str, video_filepath: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.video_filepath = prepare_filepath(video_filepath)

    def get_content_for_user(self) -> str:
        return f"Video: {self.video_filepath}"

    def get_content_for_assistant(self) -> str:
        return self.video_filepath

    def to_json(self) -> dict:
        return {
            "type": "video",
            "video_filepath": self.video_filepath,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "VideoMessage":
        return VideoMessage(
            author=json_data["author"],
            video_filepath=json_data["video_filepath"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class EmbeddedPDFMessage(Message):
    """Class for messages that are embedded PDFs"""

    pdf_filepath: str
    pages: list[int] | None

    def __init__(
        self,
        *,
        author: str,
        pdf_filepath: str,
        timestamp: datetime | None = None,
        pages: list[int] | None = None,
    ):
        super().__init__(author=author, timestamp=timestamp)
        self.pdf_filepath = prepare_filepath(pdf_filepath)
        self.pages = pages

    def get_content_for_user(self) -> str:
        return f"PDF: {self.pdf_filepath}"

    def get_content_for_assistant(self) -> dict:
        return {
            "pdf_filepath": self.pdf_filepath,
            "pages": self.pages,
        }

    def to_json(self) -> dict:
        return {
            "type": "pdf",
            "pdf_filepath": self.pdf_filepath,
            "pages": self.pages,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "EmbeddedPDFMessage":
        return EmbeddedPDFMessage(
            author=json_data["author"],
            pdf_filepath=json_data["pdf_filepath"],
            pages=json_data["pages"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )

    @staticmethod
    def build_from_line(author: str, raw_line: str) -> "EmbeddedPDFMessage":
        """
        Build a EmbeddedPDFMessage from a line of user input.
        Input format: <pdf_filepath> {<page_number>, <page_number>:<page_number>, ...}
        Page numbers are 1-indexed.
        It can be individual pages or ranges of pages.
        pdf_filepath might contain spaces.
        """
        raw_line = raw_line.strip()
        if raw_line.endswith("}"):
            pdf_filepath, pages_marker = raw_line[:-1].rsplit("{", 1)
            pdf_filepath = pdf_filepath.strip()
            pages_marker = pages_marker.strip()

            pages = []
            for page_or_range in pages_marker.split(","):
                page_or_range = page_or_range.strip()
                if "-" in page_or_range:
                    start, end = page_or_range.split("-")
                    pages.extend(range(int(start), int(end) + 1))
                elif ":" in page_or_range:
                    start, end = page_or_range.split(":")
                    pages.extend(range(int(start), int(end) + 1))
                else:
                    pages.append(int(page_or_range))
        else:
            pdf_filepath = raw_line
            pages = []
        return EmbeddedPDFMessage(author=author, pdf_filepath=pdf_filepath, pages=pages)


@dataclass(init=False)
class TextualFileMessage(Message):
    """
    Class for messages that are textual files
    Supports both real files with path, and virtual files that have only content.
    """

    text_filepath: str | None
    textual_content: str | None
    file_role: str | None
    name: str | None

    def __init__(
        self,
        *,
        author: str,
        text_filepath: str | None,
        textual_content: str | None,
        timestamp: datetime | None = None,
        file_role: str | None = None,
        name: str | None = None,
    ):
        super().__init__(author=author, timestamp=timestamp)
        self.text_filepath = None
        if text_filepath:
            self.text_filepath = prepare_filepath(remove_quotes(text_filepath))
        self.textual_content = textual_content
        self.file_role = file_role
        self.name = name

    def get_content_for_user(self) -> str:
        if self.textual_content:
            return f"Text file with content: {self.textual_content[:200]}"

        if os.path.isdir(self.text_filepath):
            return f"Directory: {self.text_filepath}"
        return f"Text file: {self.text_filepath}"

    def get_content_for_assistant(self) -> dict[str, str]:
        return {
            "textual_content": self.textual_content,
            "text_filepath": self.text_filepath,
        }

    def to_json(self) -> dict:
        return {
            "type": "textual_file",
            "text_filepath": self.text_filepath,
            "textual_content": self.textual_content,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "file_role": self.file_role,
            "name": self.name,
        }

    @staticmethod
    def from_json(json_data: dict) -> "TextualFileMessage":
        return TextualFileMessage(
            author=json_data["author"],
            text_filepath=json_data["text_filepath"],
            textual_content=json_data.get("textual_content"),
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            file_role=json_data.get("file_role"),
            name=json_data.get("name"),
        )


@dataclass(init=False)
class LLMRunCommandOutput(Message):
    """Class for messages that represent the output of LLM-run commands"""

    text: str
    name: str | None

    def __init__(
        self,
        *,
        text: str,
        timestamp: datetime | None = None,
        name: str | None = None,
    ):
        super().__init__(author="user", timestamp=timestamp)
        self.text = text
        self.name = name

    def get_content_for_user(self) -> str:
        return f"LLM Run Command Output: {self.text}"

    def get_content_for_assistant(self) -> str:
        return self.text

    def to_json(self) -> dict:
        return {
            "type": "llm_run_command_output",
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
        }

    @staticmethod
    def from_json(json_data: dict) -> "LLMRunCommandOutput":
        return LLMRunCommandOutput(
            text=json_data["text"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            name=json_data.get("name"),
        )


@dataclass(init=False)
class UrlMessage(Message):
    """Class for messages that are urls"""

    url: str

    def __init__(self, *, author: str, url: str, timestamp: datetime | None = None):
        super().__init__(author=author, timestamp=timestamp)
        self.url = url

    def get_content_for_user(self) -> str:
        return f"URL: {self.url}"

    def get_content_for_assistant(self) -> str:
        return self.url

    def to_json(self) -> dict:
        return {
            "type": "url",
            "url": self.url,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict) -> "UrlMessage":
        return UrlMessage(
            author=json_data["author"],
            url=json_data["url"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass(init=False)
class ThinkingAndResponseGeneratorMessage(Message):
    """Class for messages that contain both thinking and response generators"""

    thinking_and_response_generator: Generator[BaseLLMResponse, None, None]
    thinking_text: str
    response_text: str
    thinking_finished: bool
    response_finished: bool
    is_directly_entered: bool
    name: str
    text_role: str

    def __init__(
        self,
        *,
        author: str,
        thinking_and_response_generator: Generator[BaseLLMResponse, None, None],
        timestamp: datetime | None = None,
        is_directly_entered=False,
        name: str = "",
        text_role: str = "",
    ):
        super().__init__(author=author, timestamp=timestamp)
        self.thinking_and_response_generator = PeekableGenerator(thinking_and_response_generator)
        self.thinking_text = ""
        self.response_text = ""
        self.thinking_informed = False
        self.thinking_finished = False
        self.response_finished = False
        self.is_directly_entered = is_directly_entered
        self.name = name
        self.text_role = text_role

    def get_content_for_user(self) -> Generator[str, None, None]:
        if self.thinking_text:
            yield self.thinking_text
        if not self.thinking_finished:
            for line in chunks_to_lines(
                chunk.text
                for chunk in iterate_while(
                    self.thinking_and_response_generator,
                    lambda chunk: isinstance(chunk, ThinkingLLMResponse),
                )
            ):
                if not self.thinking_informed:
                    yield "> Thinking...\n"
                    self.thinking_informed = True
                self.thinking_text += line
                yield "> " + line
            self.thinking_finished = True
        if self.thinking_text:
            yield """
> Thinking finished
---
"""
        if self.response_text:
            yield self.response_text
        if not self.response_finished:
            for chunk in self.thinking_and_response_generator:
                self.response_text += chunk.text
                yield chunk.text
            self.response_finished = True

    def get_content_for_assistant(self) -> str:
        # Process remaining chunks if any
        if not self.thinking_finished:
            for chunk in iterate_while(
                self.thinking_and_response_generator,
                lambda chunk: isinstance(chunk, ThinkingLLMResponse),
            ):
                self.thinking_text += chunk.text
            self.thinking_finished = True
        if not self.response_finished:
            for chunk in self.thinking_and_response_generator:
                self.response_text += chunk.text
            self.response_finished = True
        return self.thinking_text + "\n" + self.response_text

    def to_json(self) -> dict:
        return {
            "type": "thinking_and_response_generator",
            "thinking_text": self.thinking_text,
            "response_text": self.response_text,
            "thinking_finished": self.thinking_finished,
            "response_finished": self.response_finished,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "is_directly_entered": self.is_directly_entered,
            "name": self.name,
            "text_role": self.text_role,
        }

    @staticmethod
    def from_json(json_data: dict) -> "ThinkingAndResponseGeneratorMessage":
        def gen_thinking_and_response():
            yield from []

        def gen_response():
            yield from []

        msg = ThinkingAndResponseGeneratorMessage(
            author=json_data["author"],
            thinking_and_response_generator=gen_thinking_and_response(),
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            is_directly_entered=json_data.get("is_directly_entered", False),
            name=json_data.get("name", ""),
            text_role=json_data.get("text_role", ""),
        )
        msg.thinking_text = json_data["thinking_text"]
        msg.response_text = json_data["response_text"]
        msg.thinking_finished = True
        msg.response_finished = True
        return msg


@dataclass(init=False)
class AssistantNotificationMessage(TextMessage):
    """Class for notifications visible only to the assistant, not the user"""

    def __init__(
        self,
        *,
        text: str,
        timestamp: datetime | None = None,
        name: str | None = None,
    ):
        super().__init__(
            author="user",
            text=text,
            timestamp=timestamp,
            is_directly_entered=True,
            name=name,
            text_role="notification",
        )

    def get_content_for_user(self) -> str:
        # Not visible to the user
        return ""

    def to_json(self) -> dict:
        data = super().to_json()
        data["type"] = "assistant_notification"
        return data

    @staticmethod
    def from_json(json_data: dict) -> "AssistantNotificationMessage":
        return AssistantNotificationMessage(
            text=json_data["text"],
            timestamp=datetime.fromisoformat(json_data["timestamp"]),
            name=json_data.get("name"),
        )


DESERIALIZATION_KEYMAP = {
    "llm_run_command_output": LLMRunCommandOutput.from_json,
    "text": TextMessage.from_json,
    "text_generator": TextGeneratorMessage.from_json,
    "invisible": InvisibleMessage.from_json,
    "image_url": ImageUrlMessage.from_json,
    "image": ImageMessage.from_json,
    "audio": AudioFileMessage.from_json,
    "video": VideoMessage.from_json,
    "pdf": EmbeddedPDFMessage.from_json,
    "textual_file": TextualFileMessage.from_json,
    "url": UrlMessage.from_json,
    "thinking_and_response_generator": ThinkingAndResponseGeneratorMessage.from_json,
    "assistant_notification": AssistantNotificationMessage.from_json,
}
