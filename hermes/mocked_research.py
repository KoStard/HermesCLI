"""Entry point for running Deep Research with mocked LLM responses for testing"""

import logging
from argparse import Namespace
from collections.abc import Generator
from pathlib import Path

from hermes.chat.conversation_orchestrator import ConversationOrchestrator
from hermes.chat.history import History
from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator
from hermes.chat.interface.assistant.framework.llm_interface import LLMInterface
from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.chat.interface.control_panel.commands_lister import CommandsLister
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.participants.debug_participant import DebugParticipant
from hermes.chat.participants.llm_participant import LLMParticipant
from hermes.cli_parser import CLIParser
from hermes.components_container import CoreComponents
from hermes.config_manager import ConfigManager
from hermes.core_components_builder import CoreComponentsBuilder
from hermes.participants_factory import ParticipantsFactory
from hermes.utils_command_executor import UtilsCommandExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockedLLMInterface(LLMInterface):
    """Mocked LLM interface that reads responses from a file instead of calling an actual LLM"""

    def __init__(self, mock_file_path: Path):
        self.mock_file_path = mock_file_path
        self.responses: list[str] = []
        self.current_response_index = 0
        self._load_responses()

    def _load_responses(self):
        """Load mocked responses from the file, split by $%%"""
        if not self.mock_file_path.exists():
            raise FileNotFoundError(f"Mock file not found: {self.mock_file_path}")

        content = self.mock_file_path.read_text()
        # Split by $%% and strip whitespace
        self.responses = [response.strip() for response in content.split("$%%") if response.strip()]
        logger.info(f"Loaded {len(self.responses)} mocked responses from {self.mock_file_path}")

    def generate_request(self, history_messages: list[dict]) -> dict:
        """Generate a mock request - just returns a placeholder"""
        return {"mock": True, "history_length": len(history_messages)}

    def send_request(self, request: dict) -> Generator[str, None, None]:
        """Return the next mocked response"""
        if self.current_response_index >= len(self.responses):
            logger.warning("No more mocked responses available, returning empty response")
            yield ""
            return

        response = self.responses[self.current_response_index]
        self.current_response_index += 1
        logger.debug(f"Returning mocked response {self.current_response_index}/{len(self.responses)}")

        # Yield the response character by character to simulate streaming
        yield from response


class MockedChatModel(ChatModel):
    """Minimal ChatModel implementation for mocked testing"""

    def __init__(self):
        # Initialize with empty values since we won't use them
        super().__init__({}, "mock", CLINotificationsPrinter())

    def initialize(self):
        pass

    def get_request_builder(self):
        # Return a dummy request builder since we're not using it
        return None

    def send_request(self, request: dict):
        # Forward the request to our mocked interface
        pass

    @staticmethod
    def get_provider() -> str:
        return "MOCK"

    @staticmethod
    def get_model_tags() -> list[str]:
        return ["mock"]


class MockApplicationOrchestrator:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.core_components_builder = CoreComponentsBuilder(self.config_manager, self.config_manager.get_command_status_overrides())
        self.participants_factory = ParticipantsFactory(self.config_manager)

    def run(self):
        components = self.core_components_builder.build()
        provider_model_pairs = components.model_factory.get_provider_model_pairs()
        cli_parser = CLIParser(provider_model_pairs)
        cli_parser.add_user_control_panel_arguments(components.user_control_panel)
        extension_utils_visitors = cli_parser.register_utility_extensions_and_get_executor_visitors(components.extension_utils_builders)

        cli_args = cli_parser.parse_args()
        self.core_components_builder.setup_logging(cli_args.verbose)
        self._execute_based_on_mode(cli_args.execution_mode, cli_args, components, extension_utils_visitors)

    def _execute_based_on_mode(self, execution_mode: str, cli_args: Namespace, components: CoreComponents, extension_utils_visitors: list):  # noqa: C901
        # if execution_mode == "info":
        #     self._execute_info_mode(cli_args, components)
        # if execution_mode == "utils":
        #     self._execute_utils_mode(cli_args, extension_utils_visitors)
        # if execution_mode == "chat":
        #     self._execute_chat_mode(cli_args, components)
        # if execution_mode == "simple-agent":
        #     self._execute_simple_agent_mode(cli_args, components)
        if execution_mode == "research":
            self._execute_research_mode(cli_args, components)

    def _register_extensions(self, extension_builders, utils_subparsers):
        extension_visitors = []
        for builder in extension_builders:
            extension_visitors.append(builder(utils_subparsers))
        return extension_visitors

    def _execute_simple_agent_mode(self, cli_args: Namespace, components: CoreComponents):
        # For now, simple agent mode uses the chat mode
        # TODO: Implement actual agent mode functionality
        self._execute_chat_mode(cli_args, components)

    def _execute_research_mode(self, cli_args: Namespace, components: CoreComponents):
        # For research mode, we need to set budget and run deep research
        model_info_string = self._get_model_info_string(cli_args.model)
        participants = self.participants_factory.create_participants(
            cli_args=cli_args,
            user_control_panel=components.user_control_panel,
            model_factory=components.model_factory,
            llm_control_panel=components.llm_control_panel,
            extension_deep_research_commands=components.extension_deep_research_commands,
            mcp_manager=components.mcp_manager,
            model_info_string=model_info_string,
        )
        participants.assistant.orchestrator.model = MockedChatModel()
        self.participants_factory.print_welcome_message(model_info_string)

        history = History()
        conversation_orchestrator = ConversationOrchestrator(
            user_participant=participants.user,
            assistant_participant=participants.assistant,
            history=history,
            mcp_manager=components.mcp_manager,
        )

        assistant_orchestrator = conversation_orchestrator.assistant_participant.orchestrator
        if not isinstance(assistant_orchestrator, DeepResearchAssistantOrchestrator):
            raise Exception("Invalid state")

        assistant_orchestrator.get_engine().llm_interface = MockedLLMInterface(Path("hermes/examples/mock_responses.txt"))

        self._run_conversation(conversation_orchestrator, participants.assistant)

    def _execute_info_mode(self, cli_args, components):
        lister = CommandsLister()
        if cli_args.info_command == "list-assistant-commands":
            lister.print_commands(components.llm_control_panel.get_commands())
        elif cli_args.info_command == "list-user-commands":
            lister.print_commands(components.user_control_panel.get_commands())

    def _execute_utils_mode(self, cli_args, extension_visitors):
        utils_executor = UtilsCommandExecutor(self.config_manager.get_config())
        utils_executor.execute(cli_args, extension_visitors)

    def _execute_chat_mode(self, cli_args: Namespace, components: CoreComponents):
        model_info_string = self._get_model_info_string(cli_args.model)
        participants = self.participants_factory.create_participants(
            cli_args=cli_args,
            user_control_panel=components.user_control_panel,
            model_factory=components.model_factory,
            llm_control_panel=components.llm_control_panel,
            extension_deep_research_commands=components.extension_deep_research_commands,
            mcp_manager=components.mcp_manager,
            model_info_string=model_info_string,
        )
        self.participants_factory.print_welcome_message(model_info_string)

        history = History()
        conversation_orchestrator = ConversationOrchestrator(
            user_participant=participants.user,
            assistant_participant=participants.assistant,
            history=history,
            mcp_manager=components.mcp_manager,
        )
        self._run_conversation(conversation_orchestrator, participants.assistant)

    def _get_model_info_string(self, cli_model: str | None) -> str | None:
        return cli_model or self.config_manager.get_default_model_info_string()

    def _run_conversation(self, conversation_orchestrator: ConversationOrchestrator, assistant: LLMParticipant | DebugParticipant):
        try:
            conversation_orchestrator.start_conversation()
        except EOFError:
            print("\nExiting gracefully...")
        except ValueError as e:
            print("Error occurred:")
            raise e
        finally:
            self._cleanup_if_needed(assistant)

    def _cleanup_if_needed(self, assistant_participant: LLMParticipant | DebugParticipant):
        if isinstance(assistant_participant, DebugParticipant):
            assistant_participant.orchestrator.cleanup()


def main():
    MockApplicationOrchestrator().run()


if __name__ == "__main__":
    main()
