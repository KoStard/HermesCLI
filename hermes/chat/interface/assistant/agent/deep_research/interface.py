import logging
import os
from collections.abc import Generator, Sequence
from pathlib import Path

# Import other necessary types
from hermes.chat.event import Event, MessageEvent
from hermes.chat.history import History
from hermes.chat.interface import Interface
from hermes.chat.interface.assistant.agent.deep_research.commands.command_context_factory import CommandContextFactoryImpl
from hermes.chat.interface.assistant.agent.deep_research.commands.commands import register_deep_research_commands
from hermes.chat.interface.assistant.agent.deep_research.context.dynamic_sections.registry import (
    get_data_type_to_renderer_instance_map,
)
from hermes.chat.interface.assistant.agent.deep_research.context.interface import DeepResearcherInterface
from hermes.chat.interface.assistant.agent.deep_research.report.report_generator import ReportGeneratorImpl
from hermes.chat.interface.assistant.agent.deep_research.report.status_printer import StatusPrinterImpl
from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicDataTypeToRendererMap
from hermes.chat.interface.assistant.agent.framework.engine import AgentEngine
from hermes.chat.interface.assistant.agent.framework.llm_interface_impl import (
    ChatModelLLMInterface,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel

# Import core command components
from hermes.chat.interface.commands.command import CommandRegistry
from hermes.chat.interface.commands.help_generator import CommandHelpGenerator
from hermes.chat.interface.templates.template_manager import TemplateManager
from hermes.chat.message import Message, TextMessage, TextualFileMessage
from hermes.utils.file_reader import FileReader

logger = logging.getLogger(__name__)


class DeepResearchAssistantInterface(Interface):
    """Interface for the Deep Research Assistant"""

    def __init__(self, model: ChatModel, research_path: Path, extension_commands=None):
        self.model = model
        self.model.initialize()

        llm_interface = ChatModelLLMInterface(self.model, research_path)
        self.command_registry = CommandRegistry()

        if extension_commands:
            for cmd_def in extension_commands:
                self.command_registry.register(cmd_def)

        register_deep_research_commands(self.command_registry)

        templates_dir = Path(__file__).parent / "templates"
        template_manager = TemplateManager(templates_dir)
        commands_help_generator = CommandHelpGenerator()
        command_context_factory = CommandContextFactoryImpl()
        renderer_registry: DynamicDataTypeToRendererMap = get_data_type_to_renderer_instance_map(template_manager)
        research_interface = DeepResearcherInterface(
            template_manager,
            commands_help_generator,
            self.command_registry,
        )
        report_generator = ReportGeneratorImpl(template_manager)
        status_printer = StatusPrinterImpl(template_manager)

        # Create the engine, passing the command registry
        self._engine: AgentEngine = AgentEngine(
            research_path,
            llm_interface,
            self.command_registry,
            command_context_factory,
            template_manager,
            renderer_registry,
            research_interface,
            report_generator,
            status_printer
        )

        self._instruction = None
        self._history_has_been_imported = False

    def render(self, history_snapshot: list[Message], events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        """Render the interface with the given history and events"""
        logger.debug("Rendering Deep Research Assistant interface")

        instruction_pieces = []
        textual_files = []

        # Initialize the engine if it doesn't exist yet
        if not self._history_has_been_imported:
            self._add_data_from_messages(history_snapshot, textual_files, instruction_pieces)
            self._history_has_been_imported = True

        # Process new messages and file uploads
        messages = [event.get_message() for event in events if isinstance(event, MessageEvent)]
        self._add_data_from_messages(messages, textual_files, instruction_pieces)

        self._instruction = "\n".join(instruction_pieces)

        for filename, file_content in textual_files:
            self._engine.research.get_external_file_manager().add_external_file(filename, file_content)

        # No need to yield anything here as we'll process in get_input
        yield from []

    def _add_data_from_messages(self, messages: Sequence[Message], textual_files: list, instruction_pieces: list):
        for message in messages:
            if message.author == "user":
                if isinstance(message, TextualFileMessage):
                    file_details = self._process_textual_file_message(message)
                    if file_details:
                        textual_files.append(file_details)
                else:
                    instruction_pieces.append(message.get_content_for_assistant())

    def _process_textual_file_message(self, message: TextualFileMessage):
        """Process a TextualFileMessage, saving it as an external file"""
        file_content = message.textual_content

        # If the message has a filepath but no content, try to read it
        if not file_content and message.text_filepath:
            file_content, success = FileReader.read_file(message.text_filepath)
            if not success:
                logger.error(f"Failed to read file {message.text_filepath}")
                return

        if file_content:
            # Use the filename from message or derive from text_filepath
            filename = message.name
            if not filename and message.text_filepath:
                filename = os.path.basename(message.text_filepath)
            if not filename:
                filename = f"external_file_{str(hash(str(file_content)))[:8]}.md"  # Add extension for clarity

            return filename, file_content
        return None  # Return None if no content

    def get_input(self) -> Generator[Event, None, None]:
        """
        Process instructions and drive the Deep Research Engine execution cycles.
        Yields status messages based on the engine's state.
        """
        logger.debug("Processing instruction in Deep Research Assistant")

        # Ensure engine is initialized (should be done by render)
        if not self._history_has_been_imported:
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
                if self._instruction:
                    logger.info("Defining root problem.")
                    self._engine.define_root_problem(self._instruction)

                    # Root problem defined, start execution immediately
                    logger.info("Executing initial research.")
                    self._engine.execute()  # Runs until awaiting_new_instruction is True
                    # Check if the root node finished/failed to generate the final report
                    root_node = self._engine.research.get_root_node()
                    if root_node.get_problem_status() in [
                        ProblemStatus.FINISHED,
                        ProblemStatus.FAILED,
                    ]:
                        logger.info("Generating final report.")
                        final_report = self._engine._generate_final_report()
                        yield MessageEvent(TextMessage(author="assistant", text=final_report))
                    # Always yield the waiting message after completion
                    yield MessageEvent(
                        TextMessage(
                            author="assistant",
                            text="Initial research complete. Waiting for next instruction...",
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
            if self._instruction:
                logger.info("Received new instruction. Preparing engine.")
                self._engine.add_new_instruction(self._instruction)
                self._instruction = None  # Clear instruction after use
                logger.info("Executing new instruction.")
                self._engine.execute()  # Runs until awaiting_new_instruction is True again
                # Check state after execution finishes
                # Check if the root node finished/failed to generate the final report
                root_node = self._engine.research.get_root_node()
                if root_node.get_problem_status() in [
                    ProblemStatus.FINISHED,
                    ProblemStatus.FAILED,
                ]:
                    logger.info("Generating final report after follow-up instruction.")
                    final_report = self._engine._generate_final_report()
                    yield MessageEvent(TextMessage(author="assistant", text=final_report))
                # Always yield the waiting message after completion
                yield MessageEvent(
                    TextMessage(
                        author="assistant",
                        text="Processing complete. Waiting for next instruction...",
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

        except Exception as e:
            logger.error(f"Error during Deep Research engine interaction: {e}", exc_info=True)
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

    def set_budget(self, budget: int):
        """Set the budget for the Deep Research Assistant"""
        self._engine.set_budget(budget)
