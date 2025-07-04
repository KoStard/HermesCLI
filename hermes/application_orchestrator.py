from argparse import Namespace

from hermes.chat.conversation_orchestrator import ConversationOrchestrator
from hermes.chat.history import History
from hermes.chat.interface.control_panel.commands_lister import CommandsLister
from hermes.chat.participants.debug_participant import DebugParticipant
from hermes.chat.participants.llm_participant import LLMParticipant
from hermes.cli_parser import CLIParser
from hermes.components_container import CoreComponents
from hermes.config_manager import ConfigManager
from hermes.core_components_builder import CoreComponentsBuilder
from hermes.participants_factory import ParticipantsFactory
from hermes.utils_command_executor import UtilsCommandExecutor


class ApplicationOrchestrator:
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
        if execution_mode == "info":
            self._execute_info_mode(cli_args, components)
        if execution_mode == "utils":
            self._execute_utils_mode(cli_args, extension_utils_visitors)
        if execution_mode == "chat":
            self._execute_chat_mode(cli_args, components)
        if execution_mode == "simple-agent":
            self._execute_simple_agent_mode(cli_args, components)
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
        self.participants_factory.print_welcome_message(model_info_string)

        history = History()
        conversation_orchestrator = ConversationOrchestrator(
            user_participant=participants.user,
            assistant_participant=participants.assistant,
            history=history,
            mcp_manager=components.mcp_manager,
        )
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
