import logging
from collections.abc import Generator
from pathlib import Path

from hermes.chat.interface.assistant.chat_assistant.response_types import (
    BaseLLMResponse,
    TextLLMResponse,
    ThinkingLLMResponse,
)
from hermes.chat.interface.assistant.deep_research_assistant.llm_interface import (
    LLMInterface,
)
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.chat.message import TextMessage

logger = logging.getLogger(__name__)


class ChatModelLLMInterface(LLMInterface):
    """Implementation of LLMInterface using ChatModel"""

    def __init__(self, model: ChatModel, research_dir: Path):
        self.model = model

    def generate_request(
        self,
        help_interface: str,
        history_messages: list[dict],
        node_path: Path,
    ) -> dict:
        """Generate a request for the LLM based on the rendered interface and history"""
        request_builder = self.model.get_request_builder()

        logging_history = list(history_messages)

        # Convert history messages to TextMessage objects
        # First the static interface
        rendered_messages = [TextMessage(author="user", text=help_interface)]
        logging_history.insert(0, {"author": "user", "content": help_interface})

        # Add history messages
        for message in history_messages:
            rendered_messages.append(TextMessage(author=message["author"], text=message["content"]))

        # Build and return the request
        request = request_builder.build_request(rendered_messages)

        return request

    def send_request(self, request: dict) -> Generator[str, None, None]:
        """Send a request to the LLM and get a generator of responses"""
        # Process the LLM response and handle thinking vs text tokens
        llm_responses_generator = self._handle_string_output(self.model.send_request(request))

        # Collect the response
        llm_response = []
        is_thinking = False
        is_working = False
        for response in llm_responses_generator:
            if isinstance(response, TextLLMResponse):
                if is_thinking:
                    print("Thinking finished")
                    is_thinking = False
                if not is_working:
                    print("Working...", end="", flush=True)
                    is_working = True
                else:
                    print(".", end="", flush=True)
                llm_response.append(response.text)
                logger.debug(response.text)
            else:
                assert isinstance(response, ThinkingLLMResponse)
                if not is_thinking:
                    is_thinking = True
                    print("Thinking...", end="", flush=True)
                else:
                    print(".", end="", flush=True)
                logger.debug(response.text)
        print()

        # Join the response parts and yield the final result
        full_llm_response = "".join(llm_response)
        yield full_llm_response

    def _handle_string_output(self, llm_response_generator: Generator[str, None, None]) -> Generator[BaseLLMResponse, None, None]:
        """
        This is implemented for backwards compatibility, as not all models support thinking tokens yet
        and they currently just return string.
        """
        for response in llm_response_generator:
            if isinstance(response, str):
                yield TextLLMResponse(response)
            else:
                yield response
