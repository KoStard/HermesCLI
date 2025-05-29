import os
from dataclasses import dataclass
from datetime import datetime

from hermes.chat.messages.base import Message
from hermes.utils.file_extension import remove_quotes
from hermes.utils.filepath import prepare_filepath


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
