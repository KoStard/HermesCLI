from argparse import Namespace

from hermes.application_initializer import ApplicationInitializer
from hermes.chat.conversation_orchestrator import ConversationOrchestrator
from hermes.chat.history import History
from hermes.chat.interface.control_panel.commands_lister import CommandsLister
from hermes.chat.participants import Participant
from hermes.cli_parser import CLIParser
from hermes.components_container import CoreComponents
from hermes.config_manager import ConfigManager
from hermes.utils_command_executor import UtilsCommandExecutor


class ApplicationOrchestrator:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.app_initializer = ApplicationInitializer(self.config_manager, self.config_manager.get_command_status_overrides())

    def run(self):
        components = self.app_initializer.get_core_components()
        provider_model_pairs = components.model_factory.get_provider_model_pairs()
        cli_parser = CLIParser(provider_model_pairs)
        cli_parser.add_user_control_panel_arguments(components.user_control_panel)

        extension_utils_visitors = cli_parser.register_utility_extensions_and_get_executor_visitors(components.extension_utils_builders)
        cli_args = cli_parser.parse_args()
        self.app_initializer.setup_logging(cli_args.verbose)

        if cli_args.execution_mode == "info":
            self._execute_info_mode(cli_args, components)
        elif cli_args.execution_mode == "utils":
            self._execute_utils_mode(cli_args, extension_utils_visitors)
        else:
            self._execute_chat_mode(cli_args, components)

    def _register_extensions(self, extension_builders, utils_subparsers):
        extension_visitors = []
        for builder in extension_builders:
            extension_visitors.append(builder(utils_subparsers))
        return extension_visitors

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
        participants = self.app_initializer.create_participants(
            cli_args=cli_args,
            user_control_panel=components.user_control_panel,
            model_factory=components.model_factory,
            llm_control_panel=components.llm_control_panel,
            extension_deep_research_commands=components.extension_deep_research_commands,
            mcp_manager=components.mcp_manager,
            model_info_string=model_info_string,
        )
        self.app_initializer.print_welcome_message(model_info_string)

        # Wait for MCP clients to load, then update the available commands.
        components.mcp_manager.wait_for_initial_load()
        assistant_interface = participants.assistant.orchestrator
        if hasattr(assistant_interface, "update_mcp_commands"):
            # This branch is for DeepResearchAssistantInterface
            assistant_interface.update_mcp_commands()
        elif hasattr(assistant_interface, "control_panel") and hasattr(assistant_interface.control_panel, "update_mcp_commands"):
            # This branch is for ChatAssistantInterface and DebugInterface
            assistant_interface.control_panel.update_mcp_commands()

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

    def _run_conversation(self, conversation_orchestrator: ConversationOrchestrator, assistant: Participant):
        try:
            conversation_orchestrator.start_conversation()
        except EOFError:
            print("\nExiting gracefully...")
        except ValueError as e:
            print("Error occurred:")
            raise e
        finally:
            self._cleanup_if_needed(assistant)

    def _cleanup_if_needed(self, assistant_participant):
        if assistant_participant and hasattr(assistant_participant, "interface") and hasattr(assistant_participant.orchestrator, "cleanup"):
            print("Cleaning up debug interface")
            assistant_participant.orchestrator.cleanup()
