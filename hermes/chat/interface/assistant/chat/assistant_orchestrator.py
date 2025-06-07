import logging
from collections.abc import Generator, Iterable
from typing import Any

from hermes.chat.events import (
    Event,
    MessageEvent,
)
from hermes.chat.events.history_recovery_event import HistoryRecoveryEvent
from hermes.chat.interface import Orchestrator
from hermes.chat.interface.assistant.chat.assistant_prompt import AssistantPromptFactory
from hermes.chat.interface.assistant.chat.control_panel import (
    ChatAssistantControlPanel,
)
from hermes.chat.interface.assistant.chat.response_types import (
    BaseLLMResponse,
    TextLLMResponse,
)
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.chat.messages import (
    TextGeneratorMessage,
    TextMessage,
    ThinkingAndResponseGeneratorMessage,
)
from hermes.utils.recording_generator import RecordingGenerator

logger = logging.getLogger(__name__)


class ChatAssistantOrchestrator(Orchestrator):
    model: ChatModel
    request: Any

    def __init__(self, model: ChatModel, control_panel: ChatAssistantControlPanel):
        self.model = model
        self._initialized = False
        self.control_panel = control_panel
        self.assistant_prompt_factory = AssistantPromptFactory()

    def render(self, events: Generator[Event, None, None]):
        logger.debug("Asked to render on LLM", self.control_panel)
        self._ensure_model_readiness()
        request_builder = self.model.get_request_builder()

        rendered_messages = []

        assistant_prompt = self.assistant_prompt_factory.build_for(
            self.control_panel.get_active_commands(), is_agent_mode=self.control_panel.is_agent_mode
        )
        rendered_messages.append(TextMessage(author="user", text=assistant_prompt))

        for event in events:
            if isinstance(event, HistoryRecoveryEvent):
                for message in event.get_messages():
                    rendered_messages.append(message)
            if not isinstance(event, MessageEvent):
                continue
            message = event.get_message()
            rendered_messages.append(message)

        self.request = request_builder.build_request(rendered_messages)
        logger.debug("Request built", self.request)

    def get_input(self) -> Generator[Event, None, None]:
        logger.debug("Sending request to LLM")
        response_message = self._send_request()
        recording_response_raw_generator = RecordingGenerator(response_message.get_content_for_user())
        yield self._build_text_generator_message_event(recording_response_raw_generator)
        collected_message = "".join(recording_response_raw_generator.collected_values)
        yield from self.control_panel.extract_and_execute_commands(collected_message)

    def _ensure_model_readiness(self):
        if not self._initialized:
            self._initialized = True
            self.model.initialize()

    def _send_request(self) -> ThinkingAndResponseGeneratorMessage:
        llm_responses_generator = self._handle_string_output(self.model.send_request(self.request))
        return ThinkingAndResponseGeneratorMessage(author="assistant", thinking_and_response_generator=llm_responses_generator)

    def _handle_string_output(
        self, llm_response_generator: Generator[str | BaseLLMResponse, None, None]
    ) -> Generator[BaseLLMResponse, None, None]:
        """
        This is implemented for backwards compatibility, as not all models support thinking tokens yet
        and they currently just return string.
        """
        for response in llm_response_generator:
            if isinstance(response, str):
                yield TextLLMResponse(response)
            else:
                yield response

    def _build_text_generator_message_event(self, response_string_generator: Iterable[str]) -> MessageEvent:
        return MessageEvent(
            TextGeneratorMessage(
                author="assistant",
                text_generator=response_string_generator,
            )
        )

    def clear(self):
        pass

    def change_thinking_level(self, level: int):
        if hasattr(self.model, "set_thinking_level"):
            self.model.set_thinking_level(level)
