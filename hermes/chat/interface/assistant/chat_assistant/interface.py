import logging
from collections.abc import Generator
from typing import Any

from hermes.chat.events import (
    Event,
    MessageEvent,
    RawContentForHistoryEvent,
)
from hermes.chat.interface import Interface
from hermes.chat.interface.assistant.chat_assistant.control_panel import (
    ChatAssistantControlPanel,
)
from hermes.chat.interface.assistant.chat_assistant.response_types import (
    BaseLLMResponse,
    TextLLMResponse,
)
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.chat.messages import (
    Message,
    TextMessage,
    ThinkingAndResponseGeneratorMessage,
)

logger = logging.getLogger(__name__)


class ChatAssistantInterface(Interface):
    model: ChatModel
    request: Any

    def __init__(self, model: ChatModel, control_panel: ChatAssistantControlPanel):
        self.model = model
        self._initialized = False
        self.control_panel = control_panel

    def render(self, history_snapshot: list[Message], events: Generator[Event, None, None]):
        if not self._initialized:
            self._initialized = True
            self.model.initialize()
        logger.debug("Asked to render on LLM", self.control_panel)
        request_builder = self.model.get_request_builder()

        rendered_messages = []

        control_panel_content = self.control_panel.render()
        if control_panel_content:
            rendered_messages.append(TextMessage(author="user", text=control_panel_content))

        help_message = self._get_help_message()
        if help_message:
            rendered_messages.append(TextMessage(author="user", text=help_message))

        for message in history_snapshot:
            rendered_messages.append(message)

        for event in events:
            if not isinstance(event, MessageEvent):
                continue
            message = event.get_message()
            rendered_messages.append(message)

        self.request = request_builder.build_request(rendered_messages)
        logger.debug("Request built", self.request)

    def get_input(self) -> Generator[Event, None, None]:
        logger.debug("Sending request to LLM")
        llm_responses_generator = self._handle_string_output(self.model.send_request(self.request))
        message = ThinkingAndResponseGeneratorMessage(author="assistant", thinking_and_response_generator=llm_responses_generator)
        yield RawContentForHistoryEvent(message)
        yield from self.control_panel.break_down_and_execute_message(message)

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

    def clear(self):
        pass

    def change_thinking_level(self, level: int):
        if hasattr(self.model, "set_thinking_level"):
            self.model.set_thinking_level(level)

    def _get_help_message(self):
        return self.model.get_request_builder().prompt_builder_factory.get_help_message()
