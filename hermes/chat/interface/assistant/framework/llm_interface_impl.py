import logging
from collections.abc import Generator

from hermes.chat.interface.assistant.framework.llm_interface import (
    LLMInterface,
)
from hermes.chat.interface.assistant.chat.response_types import (
    BaseLLMResponse,
    TextLLMResponse,
    ThinkingLLMResponse,
)
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.chat.messages import TextMessage

logger = logging.getLogger(__name__)


class ChatModelLLMInterface(LLMInterface):
    """Implementation of LLMInterface using ChatModel"""

    def __init__(self, model: ChatModel):
        self.model = model

    def generate_request(
        self,
        history_messages: list[dict],
    ) -> dict:
        """Generate a request for the LLM based on the rendered interface and history"""
        request_builder = self.model.get_request_builder()

        # Convert history messages to TextMessage objects
        rendered_messages = []

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
        is_thinking = False
        is_working = False
        for response in llm_responses_generator:
            if isinstance(response, TextLLMResponse):
                if is_thinking:
                    is_thinking = False
                if not is_working:
                    is_working = True
                yield response.text
                logger.debug(response.text)
            else:
                assert isinstance(response, ThinkingLLMResponse)
                if not is_thinking:
                    is_thinking = True
                logger.debug(response.text)

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
