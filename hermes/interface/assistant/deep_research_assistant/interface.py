import os
import logging
from typing import Generator, List, Optional
from pathlib import Path

from hermes.interface.assistant.chat_models.base import ChatModel

# Import core command components
from hermes.interface.commands.command import CommandRegistry, Command

# Import Deep Research specific components
from hermes.interface.assistant.deep_research_assistant.engine.engine import (
    DeepResearchEngine,
)
from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import (
    ProblemStatus,
)
from hermes.interface.assistant.deep_research_assistant.llm_interface_impl import (
    ChatModelLLMInterface,
)
from hermes.interface.base import Interface

# Import other necessary types
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
        # Store extension command *classes* or *instances*
        self.extension_command_defs = extension_commands or []
        self._engine: Optional[DeepResearchEngine] = None
        self.instruction = None
        self._pending_budget = None  # Store budget until engine is initialized

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

            # Create the engine *without* passing extension commands initially
            self._engine = DeepResearchEngine(
                self.research_dir,
                llm_interface,
            )

            # Register extension commands *after* engine creation
            # This ensures the core commands are registered first by the engine's command module import
            registry = CommandRegistry()
            for cmd_def in self.extension_command_defs:
                if isinstance(cmd_def, Command):
                    # If it's already an instance
                    registry.register(cmd_def)
                elif isinstance(cmd_def, type) and issubclass(cmd_def, Command):
                    # If it's a class, instantiate and register
                    try:
                        registry.register(cmd_def())
                    except Exception as e:
                        logger.error(
                            f"Failed to instantiate and register extension command {cmd_def.__name__}: {e}"
                        )
                else:
                    logger.warning(
                        f"Ignoring invalid extension command definition: {cmd_def}"
                    )

            # Apply any pending budget
            if self._pending_budget is not None:
                self._engine.set_budget(self._pending_budget)
                self._pending_budget = None

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
                filename = f"external_file_{hash(str(file_content))[:8]}.txt"  # Add extension for clarity

            return filename, file_content
        return None  # Return None if no content

    def get_input(self) -> Generator[Event, None, None]:
        """
        Process instructions and drive the Deep Research Engine execution cycles.
        Yields status messages based on the engine's state.
        """
        logger.debug("Processing instruction in Deep Research Assistant")

        # Ensure engine is initialized (should be done by render)
        if not self._engine:
            logger.error("Engine not initialized before get_input call.")
            yield MessageEvent(
                TextMessage(
                    author="assistant",
                    text="Error: Deep Research Engine not initialized.",
                )
            )
            return

        try:
            # --- Initial Problem Definition ---
            if not self._engine.is_root_problem_defined():
                if self.instruction:
                    logger.info("Defining root problem.")
                    success = self._engine.define_root_problem(self.instruction)
                    self.instruction = None  # Clear instruction after use
                    if not success:
                        yield MessageEvent(
                            TextMessage(
                                author="assistant",
                                text="Failed to define the root problem.",
                            )
                        )
                        return
                    else:
                        # Root problem defined, start execution immediately
                        logger.info("Executing initial research.")
                        self._engine.execute()  # Runs until awaiting_new_instruction is True
                        # Check state after execution finishes
                        if self._engine.is_awaiting_instruction():
                            # Check if the root node finished/failed to generate the final report
                            if (
                                self._engine.current_node
                                == self._engine.file_system.root_node
                                and self._engine.current_node.status
                                in [ProblemStatus.FINISHED, ProblemStatus.FAILED]
                            ):
                                logger.info("Generating final report.")
                                final_report = self._engine._generate_final_report()
                                yield MessageEvent(
                                    TextMessage(author="assistant", text=final_report)
                                )
                            # Always yield the waiting message after completion
                            yield MessageEvent(
                                TextMessage(
                                    author="assistant",
                                    text="Initial research complete. Waiting for next instruction...",
                                )
                            )
                        else:
                            logger.error(
                                "Engine did not enter awaiting state after initial execution."
                            )
                            yield MessageEvent(
                                TextMessage(
                                    author="assistant",
                                    text="Initial research finished unexpectedly. Please check logs.",
                                )
                            )
                        return  # End processing for this call
                else:
                    # No root problem and no instruction provided
                    yield MessageEvent(
                        TextMessage(
                            author="assistant",
                            text="Please provide an initial research instruction.",
                        )
                    )
                    return  # End processing for this call

            # --- Continuous Interaction Cycle ---
            # Engine exists and root problem is defined. Check state.
            if self._engine.is_awaiting_instruction():
                if self.instruction:
                    logger.info("Received new instruction. Preparing engine.")
                    self._engine.prepare_for_new_instruction(self.instruction)
                    self.instruction = None  # Clear instruction after use
                    logger.info("Executing new instruction.")
                    self._engine.execute()  # Runs until awaiting_new_instruction is True again
                    # Check state after execution finishes
                    if self._engine.is_awaiting_instruction():
                        # Check if the root node finished/failed to generate the final report
                        if (
                            self._engine.current_node
                            == self._engine.file_system.root_node
                            and self._engine.current_node.status
                            in [ProblemStatus.FINISHED, ProblemStatus.FAILED]
                        ):
                            logger.info(
                                "Generating final report after follow-up instruction."
                            )
                            final_report = self._engine._generate_final_report()
                            yield MessageEvent(
                                TextMessage(author="assistant", text=final_report)
                            )
                        # Always yield the waiting message after completion
                        yield MessageEvent(
                            TextMessage(
                                author="assistant",
                                text="Processing complete. Waiting for next instruction...",
                            )
                        )
                    else:
                        logger.error(
                            "Engine did not enter awaiting state after processing new instruction."
                        )
                        yield MessageEvent(
                            TextMessage(
                                author="assistant",
                                text="Processing finished unexpectedly. Please check logs.",
                            )
                        )
                    return  # End processing for this call
                else:
                    # Awaiting but no new instruction provided in this call
                    logger.info("Engine is awaiting instruction.")
                    yield MessageEvent(
                        TextMessage(
                            author="assistant",
                            text="Research complete. Waiting for next instruction...",
                        )
                    )
                    return  # End processing for this call
            else:
                # Engine is not awaiting instruction. This implies it might still be running
                # from a previous call, or an error occurred.
                # In a synchronous model where execute() blocks, this state shouldn't be reached
                # unless get_input is called again before execute finishes.
                logger.warning(
                    "get_input called while engine is not awaiting instruction."
                )
                yield MessageEvent(
                    TextMessage(
                        author="assistant",
                        text="Engine is currently processing. Please wait.",
                    )
                )
                return  # End processing for this call

        except Exception as e:
            logger.error(
                f"Error during Deep Research engine interaction: {e}", exc_info=True
            )
            yield MessageEvent(
                TextMessage(
                    author="assistant", text=f"An error occurred during research: {e}"
                )
            )

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

    def set_budget(self, budget: int):
        """Set the budget for the Deep Research Assistant"""
        if self._engine:
            self._engine.set_budget(budget)
        else:
            # Store the budget to be set when the engine is initialized
            self._pending_budget = budget
