import os
import logging
from typing import Generator, List
from pathlib import Path

from hermes.interface.assistant.chat_models.base import ChatModel
from hermes.interface.assistant.deep_research_assistant.engine.engine import (
    DeepResearchEngine,
)
from hermes.interface.assistant.deep_research_assistant.llm_interface_impl import (
    ChatModelLLMInterface,
)
from hermes.interface.base import Interface
from hermes.event import Event, MessageEvent
from hermes.message import Message, TextMessage
from hermes.history import History


logger = logging.getLogger(__name__)


class DeepResearchAssistantInterface(Interface):
    """Interface for the Deep Research Assistant"""

    def __init__(
        self, model: ChatModel, research_path: str = None, extension_commands=None
    ):
        self.model = model
        self.model.initialize()
        self.instruction = None
        self.research_dir = research_path if research_path else str(Path.cwd())
        self.extension_commands = extension_commands or []

    def render(
        self, history_snapshot: List[Message], events: Generator[Event, None, None]
    ) -> Generator[Event, None, None]:
        """Render the interface with the given history and events"""
        logger.debug("Rendering Deep Research Assistant interface")

        instruction = []

        for message in history_snapshot:
            if message.author == "user":
                instruction.append(message.get_content_for_assistant())

        # TODO: Likely issues here, investigate
        # Extract the instruction from the last user message
        for event in events:
            if isinstance(event, MessageEvent):
                message = event.get_message()
                if message.author == "user":
                    instruction.append(message.get_content_for_assistant())

        self.instruction = "\n".join(instruction)

        # No need to yield anything here as we'll process in get_input
        yield from []

    def get_input(self) -> Generator[Event, None, None]:
        """Process the instruction and generate a response"""
        logger.debug("Processing instruction in Deep Research Assistant")

        # Create the LLM interface
        llm_interface = ChatModelLLMInterface(self.model, self.research_dir)

        # Create and execute the engine
        engine = DeepResearchEngine(
            self.instruction,
            self.research_dir,
            llm_interface,
            self.extension_commands,
        )

        # Execute the engine and yield the results
        final_summary = engine.execute()

        # Return the summary of artifacts as an event
        yield MessageEvent(TextMessage(author="assistant", text=final_summary))

    def clear(self):
        """Clear the interface state"""
        print("Clear in deep research assistant not supported")

    def initialize_from_history(self, history: History):
        """Initialize the interface from history"""
        # Nothing to do here for now
        print("initialize_from_history in deep research assistant not supported")

    def change_thinking_level(self, level: str):
        if hasattr(self.model, "set_thinking_level"):
            self.model.set_thinking_level(level)