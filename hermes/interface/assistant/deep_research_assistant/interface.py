import os
import logging
from typing import Generator, List
from pathlib import Path

from hermes.interface.assistant.chat_assistant.response_types import BaseLLMResponse, TextLLMResponse
from hermes.interface.assistant.chat_models.base import ChatModel
from hermes.interface.assistant.deep_research_assistant.engine.engine import DeepResearchEngine
from hermes.interface.base import Interface
from hermes.event import Event, MessageEvent
from hermes.message import Message, TextMessage
from hermes.history import History


logger = logging.getLogger(__name__)


class DeepResearchAssistantInterface(Interface):
    """Interface for the Deep Research Assistant"""

    def __init__(self, model: ChatModel):
        self.model = model
        self.model.initialize()
        self.instruction = None
        self.attachments = []
        self.research_dir = os.path.join(str(Path.cwd()), "deep_research")

    def render(
        self, history_snapshot: List[Message], events: Generator[Event, None, None]
    ) -> Generator[Event, None, None]:
        """Render the interface with the given history and events"""
        logger.debug("Rendering Deep Research Assistant interface")
        
        instruction = []
        
        # TODO: Likely issues here, investigate
        # Extract the instruction from the last user message
        for event in events:
            if isinstance(event, MessageEvent):
                message = event.get_message()
                if message.author == "user":
                    instruction.append(message.get_content_for_assistant())
        
        self.instruction = '\n'.join(instruction)
        
        # No need to yield anything here as we'll process in get_input
        yield from []

    def get_input(self) -> Generator[Event, None, None]:
        """Process the instruction and generate a response"""
        logger.debug("Processing instruction in Deep Research Assistant")
        request_builder = self.model.get_request_builder()
        
        report = None
        
        engine = DeepResearchEngine(self.instruction, self.attachments, self.research_dir)
        
        while not engine.finished:
            rendered_messages = []
            
            # Render the messages
            rendered_messages.append(TextMessage(author="user", text=engine.get_interface_content()))
            
            for message in engine.chat_history.messages:
                rendered_messages.append(
                    TextMessage(author=message.author, text=message.content)
                )
            
            request = request_builder.build_request(rendered_messages)
            
            llm_responses_generator = self._handle_string_output(
                self.model.send_request(request)
            )
            llm_response = []
            is_thinking = False
            for response in llm_responses_generator:
                if isinstance(response, TextLLMResponse):
                    if is_thinking:
                        print("Thinking finished")
                        print("======================")
                    llm_response.append(response.text)
                else:
                    if not is_thinking:
                        is_thinking = True
                print(response.text, end="", flush=True)
            full_llm_response = "".join(llm_response)
            engine.process_commands(full_llm_response)
        
        # Return the report as the response
        yield MessageEvent(
            TextMessage(
                author="assistant",
                text=report
            )
        )
        
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
        """Clear the interface state"""
        print("Clear in deep research assistant not supported")
        
    def initialize_from_history(self, history: History):
        """Initialize the interface from history"""
        # Nothing to do here for now
        print("initialize_from_history in deep research assistant not supported")
