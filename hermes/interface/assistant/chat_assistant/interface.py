import logging
from typing import Generator, List

from hermes.interface.assistant.chat_models.base import ChatModel
from hermes.interface.assistant.chat_assistant.control_panel import ChatAssistantControlPanel
from hermes.interface.assistant.chat_assistant.response_types import (
    BaseLLMResponse,
    TextLLMResponse,
)

from hermes.interface.base import Interface
from hermes.event import (
    Event,
    MessageEvent,
    NotificationEvent,
    RawContentForHistoryEvent,
)
from hermes.message import (
    Message,
    TextGeneratorMessage,
    TextMessage,
    ThinkingAndResponseGeneratorMessage,
)

logger = logging.getLogger(__name__)


class ChatAssistantInterface(Interface):
    model: ChatModel
    request: any

    def __init__(self, model: ChatModel, control_panel: ChatAssistantControlPanel):
        self.model = model
        self.model.initialize()
        self.control_panel = control_panel

    def render(
        self, history_snapshot: List[Message], events: Generator[Event, None, None]
    ) -> Generator[Event, None, None]:
        logger.debug("Asked to render on LLM", self.control_panel)
        request_builder = self.model.get_request_builder()

        rendered_messages = []

        control_panel_content = self.control_panel.render()
        if control_panel_content:
            rendered_messages.append(
                TextMessage(author="user", text=control_panel_content)
            )

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
        yield from []

    def get_input(self) -> Generator[Event, None, None]:
        logger.debug("Sending request to LLM")
        llm_responses_generator = self._handle_string_output(
            self.model.send_request(self.request)
        )
        message = ThinkingAndResponseGeneratorMessage(
            author="assistant", thinking_and_response_generator=llm_responses_generator
        )
        yield RawContentForHistoryEvent(message)
        for event in self.control_panel.break_down_and_execute_message(message):
            yield event

    def _handle_string_output(
        self, llm_response_generator: Generator[str, None, None]
    ) -> Generator[BaseLLMResponse, None, None]:
        """
        This is implemented for backwards compatibility, as not all models support thinking tokens yet and they currently just return string.
        """
        for response in llm_response_generator:
            if isinstance(response, str):
                yield TextLLMResponse(response)
            else:
                yield response

    def clear(self):
        pass

    def change_thinking_level(self, level: str):
        if hasattr(self.model, "set_thinking_level"):
            self.model.set_thinking_level(level)

    def _get_help_message(self):
        return (
            self.model.get_request_builder().prompt_builder_factory.get_help_message()
        )
