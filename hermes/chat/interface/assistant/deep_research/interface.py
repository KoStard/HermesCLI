import logging
import os
from collections.abc import Generator, Sequence
from pathlib import Path

# Import other necessary types
from hermes.chat.events import Event, MessageEvent
from hermes.chat.history import History
from hermes.chat.interface import Interface
from hermes.chat.interface.assistant.deep_research.commands.command_context_factory import CommandContextFactoryImpl
from hermes.chat.interface.assistant.deep_research.commands.commands import register_deep_research_commands
from hermes.chat.interface.assistant.deep_research.context.dynamic_sections.registry import (
    get_data_type_to_renderer_instance_map,
)
from hermes.chat.interface.assistant.deep_research.context.interface import DeepResearcherInterface
from hermes.chat.interface.assistant.deep_research.report.report_generator import ReportGeneratorImpl
from hermes.chat.interface.assistant.deep_research.report.status_printer import StatusPrinterImpl
from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicDataTypeToRendererMap
from hermes.chat.interface.assistant.deep_research.engine import ResearchEngine
from hermes.chat.interface.assistant.framework.llm_interface_impl import (
    ChatModelLLMInterface,
)
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.mcp.mcp_manager import McpManager

# Import core command components
from hermes.chat.interface.commands.command import CommandRegistry
from hermes.chat.interface.commands.help_generator import CommandHelpGenerator
from hermes.chat.interface.templates.template_manager import TemplateManager
from hermes.chat.messages import Message, TextMessage, TextualFileMessage
from hermes.utils.file_reader import FileReader

logger = logging.getLogger(__name__)


class DeepResearchAssistantInterface(Interface):
    """Interface for the Deep Research Assistant"""

    def __init__(
        self,
        model: ChatModel,
        research_path: Path,
        extension_commands: list | None,
        mcp_manager: McpManager,
        research_name: str | None = None,
    ):
        self.model = model
        self.mcp_manager = mcp_manager

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
        self._engine: ResearchEngine = ResearchEngine(
            research_path,
            llm_interface,
            self.command_registry,
            command_context_factory,
            template_manager,
            renderer_registry,
            research_interface,
            report_generator,
            status_printer,
            research_name=research_name,
        )

        self._initialized = False
        self._instruction: str | None = None
        self._history_has_been_imported = False

    def render(self, history_snapshot: list[Message], events: Generator[Event, None, None]):
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

    def _add_data_from_messages(self, messages: Sequence[Message], textual_files: list, instruction_pieces: list):
        for message in messages:
            if message.author == "user":
                if isinstance(message, TextualFileMessage):
                    file_details = self._process_textual_file_message(message)
                    if file_details:
                        textual_files.extend(file_details)
                else:
                    instruction_pieces.append(message.get_content_for_assistant())

    def _process_textual_file_message(self, message: TextualFileMessage) -> list[tuple]:
        """Process a TextualFileMessage, saving it as an external file"""
        file_content = message.textual_content
        filename = message.name

        if file_content:
            return self._ingest_file_with_provided_content(filename, message.text_filepath, file_content)

        if message.text_filepath:
            filepath = Path(message.text_filepath)
            if filepath.is_dir():
                return self._ingest_directory_external_files(filepath)
            else:
                return self._ingest_external_file(filepath)

        return []

    def _ingest_file_with_provided_content(self, filename: str | None, filepath: str | None, content: str) -> list[tuple]:
        if not filename and filepath:
            filename = os.path.basename(filepath)
        if not filename:
            filename = f"external_file_{str(hash(str(content)))[:8]}.md"  # Add extension for clarity
        return [(filename, content)]

    def _ingest_directory_external_files(self, filepath: Path) -> list[tuple]:
        raw_results = FileReader.read_directory(str(filepath))
        results = []
        for relative_path, content in raw_results.items():
            results.append((Path(relative_path).name, content))
        return results

    def _ingest_external_file(self, filepath: Path) -> list[tuple]:
        return [(filepath.name, FileReader.read_file(str(filepath))[0])]

    def update_mcp_commands(self):
        """Registers/updates commands from MCP clients."""
        mcp_commands = self.mcp_manager.create_commands_for_mode("deep_research")
        for command in mcp_commands:
            self.command_registry.register(command)

    def get_input(self) -> Generator[Event, None, None]:
        """
        Process instructions and drive the Deep Research Engine execution cycles.
        Yields status messages based on the engine's state.
        """
        logger.debug("Processing instruction in Deep Research Assistant")
        if not self._initialized:
            self._initialized = True
            self.model.initialize()

        if error_event := self._check_engine_initialized():
            yield error_event
            return

        try:
            if not self._engine.has_root_problem_defined():
                yield from self._handle_initial_research()
                return

            yield from self._handle_continuous_interaction()
            return

        except Exception as e:
            yield from self._handle_engine_exception(e)

    def _check_engine_initialized(self) -> Event | None:
        """Check if engine is properly initialized"""
        if not self._history_has_been_imported:
            logger.error("Engine not initialized before get_input call.")
            return MessageEvent(
                TextMessage(
                    author="assistant",
                    text="Error: Deep Research Engine not initialized.",
                )
            )
        return None

    def _handle_initial_research(self) -> Generator[Event, None, None]:
        """Handle initial research problem definition"""
        if not self._instruction:
            yield MessageEvent(
                TextMessage(
                    author="assistant",
                    text="Please provide an initial research instruction.",
                )
            )
            return

        logger.debug("Defining root problem.")
        self._engine.define_root_problem(self._instruction)

        logger.debug("Executing initial research.")
        final_report_str = self._engine.execute()

        yield from self._yield_final_report(final_report_str)
        yield from self._yield_waiting_message("Initial research complete")
        return

    def _handle_continuous_interaction(self) -> Generator[Event, None, None]:
        """Handle ongoing interaction with the research engine"""
        if not self._instruction:
            logger.debug("Engine is awaiting instruction.")
            yield from self._yield_waiting_message("Research complete")
            return

        yield from self._process_new_instruction()
        return

    def _process_new_instruction(self) -> Generator[Event, None, None]:
        """Process a new instruction from the user"""
        logger.debug("Processing new instruction")
        if self._instruction:
            self._engine.add_new_instruction(self._instruction)
            self._instruction = None  # Clear instruction after use

            logger.debug("Executing new instruction.")
            final_report_str = self._engine.execute()

            yield from self._yield_final_report(final_report_str)
        yield from self._yield_waiting_message("Processing complete")
        return

    def _yield_final_report(self, report_str: str | None) -> Generator[Event, None, None]:
        """Yield final report event if report exists"""
        if report_str:
            logger.debug("Yielding final report")
            yield MessageEvent(TextMessage(author="assistant", text=report_str))

    def _yield_waiting_message(self, prefix: str) -> Generator[Event, None, None]:
        """Yield standard waiting message"""
        yield MessageEvent(
            TextMessage(
                author="assistant",
                text=f"{prefix}. Waiting for next instruction...",
            )
        )

    def _handle_engine_exception(self, error: Exception) -> Generator[Event, None, None]:
        """Handle exceptions during engine execution"""
        logger.error(f"Error during Deep Research engine interaction: {error}", exc_info=True)
        yield MessageEvent(TextMessage(author="assistant", text=f"An error occurred during research: {error}"))

    def clear(self):
        """Clear the interface state"""
        print("Clear in deep research assistant not supported")

    def initialize_from_history(self, history: History):
        """Initialize the interface from history"""
        pass

    def change_thinking_level(self, level: int):
        if hasattr(self.model, "set_thinking_level"):
            self.model.set_thinking_level(level)

    def set_budget(self, budget: int | None):
        """Set the budget for the Deep Research Assistant"""
        self._engine.set_budget(budget)

    def create_new_research(self, name: str):
        """
        Create a new research instance under the repo and switch to it.

        Args:
            name: Name for the new research instance
        """
        self._engine.create_new_research(name)
        self._engine.switch_research(name)

    def switch_research(self, name: str):
        """
        Switch to a different research instance.

        Args:
            name: Name of the research instance to switch to
        """
        self._engine.switch_research(name)

    def list_research_instances(self) -> list[str]:
        """
        List all available research instances.

        Returns:
            List of research instance names
        """
        return self._engine.list_research_instances()

    def get_current_research_name(self) -> str | None:
        """
        Get the name of the current research instance.

        Returns:
            Name of current research instance
        """
        return self._engine.current_research_name
