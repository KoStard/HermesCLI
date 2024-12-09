import logging
from typing import Generator

from hermes.interface.assistant.chat_models.base import ChatModel

from ..base import Interface
from hermes.interface.control_panel import LLMControlPanel
from hermes.event import Event, MessageEvent, NotificationEvent
from hermes.message import Message, TextGeneratorMessage, TextMessage

logger = logging.getLogger(__name__)

class LLMInterface(Interface):
    model: ChatModel
    request: any
    
    def __init__(self, model: ChatModel, control_panel: LLMControlPanel):
        self.model = model
        self.model.initialize()
        self.control_panel = control_panel

    def render(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        logger.debug("Asked to render on LLM", self.control_panel)
        request_builder = self.model.get_request_builder()

        rendered_messages = []

        control_panel_content = self.control_panel.render()
        if control_panel_content:
            rendered_messages.append(TextMessage(author="user", text=control_panel_content))
        
        help_message = self._get_help_message()
        if help_message:
            rendered_messages.append(TextMessage(author="user", text=help_message))

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
        message = TextGeneratorMessage(author="assistant", text_generator=self.model.send_request(self.request))
        
        for event in self.control_panel.break_down_and_execute_message(message):
            yield event
    
    def clear(self):
        pass

    def _get_help_message(self):
        return self.model.get_request_builder().prompt_builder_factory.get_help_message()
