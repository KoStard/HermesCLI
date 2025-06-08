from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime

from hermes.chat.interface.assistant.chat.response_types import (
    BaseLLMResponse,
    ThinkingLLMResponse,
)
from hermes.chat.interface.helpers.chunks_to_lines import chunks_to_lines
from hermes.chat.interface.helpers.peekable_generator import PeekableGenerator, iterate_while
from hermes.chat.messages.base import Message


@dataclass(init=False)
class ThinkingAndResponseGeneratorMessage(Message):
    """Class for messages that contain both thinking and response generators"""

    thinking_and_response_generator: PeekableGenerator
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
        """Get content for user presentation, yielding both thinking and response chunks."""
        yield from self._yield_existing_thinking()
        yield from self._process_thinking_content()
        yield from self._yield_thinking_finished()
        yield from self._yield_existing_response()
        yield from self._process_response_content()

    def _yield_existing_thinking(self) -> Generator[str, None, None]:
        """Yield existing thinking text if available."""
        if self.thinking_text:
            yield self.thinking_text

    def _process_thinking_content(self) -> Generator[str, None, None]:
        """Process and yield new thinking content if thinking not finished."""
        if not self.thinking_finished:
            for line in chunks_to_lines(
                chunk.text
                for chunk in iterate_while(
                    self.thinking_and_response_generator,
                    lambda chunk: isinstance(chunk, ThinkingLLMResponse),
                )
            ):
                if not self.thinking_informed:
                    yield "> Thinking...\\n"
                    self.thinking_informed = True
                self.thinking_text += line
                yield "> " + line
            self.thinking_finished = True

    def _yield_thinking_finished(self) -> Generator[str, None, None]:
        """Yield thinking finished message if there was thinking content."""
        if self.thinking_text:
            yield """
> Thinking finished
---
"""

    def _yield_existing_response(self) -> Generator[str, None, None]:
        """Yield existing response text if available."""
        if self.response_text:
            yield self.response_text

    def _process_response_content(self) -> Generator[str, None, None]:
        """Process and yield new response content if response not finished."""
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
        return self.thinking_text + "\\n" + self.response_text

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
