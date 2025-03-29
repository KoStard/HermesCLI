import os
import logging
from typing import Generator, List, Optional
from pathlib import Path

from hermes.interface.assistant.chat_models.base import ChatModel
from hermes.interface.assistant.deep_research_assistant.engine.engine import DeepResearchEngine
from hermes.interface.assistant.deep_research_assistant.engine.hierarchy_formatter import HierarchyFormatter
from hermes.interface.assistant.deep_research_assistant.llm_interface_impl import ChatModelLLMInterface
from hermes.interface.base import Interface
from hermes.event import Event, MessageEvent
from hermes.message import Message, TextMessage, TextualFileMessage
from hermes.history import History
from hermes.utils.file_reader import FileReader


logger = logging.getLogger(__name__)


class DeepResearchAssistantInterface(Interface):
    """Interface for the Deep Research Assistant"""

    def __init__(
        self, model: ChatModel, research_path: str = None, extension_commands=None
    ):
        self.model = model
        self.model.initialize()
        self.research_dir = research_path if research_path else str(Path.cwd())
        self.extension_commands = extension_commands or []
        self._engine: Optional[DeepResearchEngine] = None
        self.hierarchy_formatter = HierarchyFormatter()
        self.instruction = None

    def render(
        self, history_snapshot: List[Message], events: Generator[Event, None, None]
    ) -> Generator[Event, None, None]:
        """Render the interface with the given history and events"""
        logger.debug("Rendering Deep Research Assistant interface")

        instruction_pieces = []
        textual_files = []
        
        # Initialize the engine if it doesn't exist yet
        if not self._engine:
            # Process all external files from history
            for message in history_snapshot:
                if message.author == "user":
                    if isinstance(message, TextualFileMessage):
                        file_details = self._process_textual_file_message(message)
                        if file_details:
                            textual_files.append(file_details)
                    else:
                        instruction_pieces.append(message.get_content_for_assistant())

        # Process new messages and file uploads
        for event in events:
            if isinstance(event, MessageEvent):
                message = event.get_message()
                if message.author == "user":
                    if isinstance(message, TextualFileMessage):
                        file_details = self._process_textual_file_message(message)
                        if file_details:
                            textual_files.append(file_details)
                    else:
                        instruction_pieces.append(message.get_content_for_assistant())

        self.instruction = "\n".join(instruction_pieces)

        if not self._engine:
            # Create LLM interface
            llm_interface = ChatModelLLMInterface(self.model, self.research_dir)

            self._engine = DeepResearchEngine(
                self.research_dir,
                llm_interface,
                self.extension_commands,
            )

        for file_details in textual_files:
            filename, file_content = file_details
            self._engine.file_system.add_external_file(filename, file_content)

        # Ensure external files are loaded/updated in the engine's file system
        self._engine.file_system.load_external_files()

        # No need to yield anything here as we'll process in get_input
        yield from []

    def _process_textual_file_message(self, message: TextualFileMessage):
        """Process a TextualFileMessage, saving it as an external file"""
        file_content = message.textual_content
        
        # If the message has a filepath but no content, try to read it
        if not file_content and message.text_filepath:
            content, success = FileReader.read_file(message.text_filepath)
            if success:
                file_content = content
            else:
                logger.error(f"Failed to read file {message.text_filepath}")
                return
        
        if file_content:
            # Use the filename from message or derive from text_filepath
            filename = message.name
            if not filename and message.text_filepath:
                filename = os.path.basename(message.text_filepath)
            if not filename:
                filename = f"external_file_{hash(str(file_content))[:8]}"

            return filename, file_content

    def get_input(self) -> Generator[Event, None, None]:
        """Process the instruction and generate a response"""
        logger.debug("Processing instruction in Deep Research Assistant")

        # The engine should already be initialized in render()
        if not self._engine:
            raise Exception("Render before running the deep research interface")
        
        try:
            # Check if root problem is defined
            if not self._engine.is_root_problem_defined():
                if not self.instruction:
                    yield MessageEvent(TextMessage(author="assistant", text="Failed to define the root problem, as no instruction provided."))
                    return
                # Define the root problem first
                success = self._engine.define_root_problem(self.instruction)
                if not success:
                    yield MessageEvent(TextMessage(author="assistant", text="Failed to define the root problem."))
                    return
            
            # Now execute the engine with the defined problem
            final_summary = self._engine.execute()

            # Return the summary of artifacts as an event
            yield MessageEvent(TextMessage(author="assistant", text=final_summary))
        except Exception as e:
             logger.error(f"Error during Deep Research engine execution: {e}", exc_info=True)
             yield MessageEvent(TextMessage(author="assistant", text=f"An error occurred during research: {e}"))


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
