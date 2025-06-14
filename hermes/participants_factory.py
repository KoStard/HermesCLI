import textwrap
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.chat.assistant_orchestrator import ChatAssistantOrchestrator
from hermes.chat.interface.assistant.chat.control_panel import ChatAssistantControlPanel
from hermes.chat.interface.assistant.models.model_factory import ModelFactory
from hermes.chat.interface.debug.debug_interface import DebugInterface
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel
from hermes.chat.interface.user.interface.command_completer.command_completer import CommandCompleter
from hermes.chat.interface.user.interface.markdown_highlighter import MarkdownHighlighter
from hermes.chat.interface.user.interface.user_interface import UserOrchestrator
from hermes.chat.participants import DebugParticipant, LLMParticipant, UserParticipant
from hermes.cli_parser import ExecutionMode
from hermes.components_container import Participants

if TYPE_CHECKING:
    from hermes.chat.interface.user.interface.stt_input_handler.stt_input_handler import STTInputHandler
    from hermes.config_manager import ConfigManager
    from hermes.mcp.mcp_manager import McpManager


class ParticipantsFactory:
    def __init__(self, config_manager: "ConfigManager"):
        self.config_manager = config_manager
        self.notifications_printer = CLINotificationsPrinter()

    def create_participants(
        self,
        cli_args: Namespace,
        user_control_panel: UserControlPanel,
        model_factory: ModelFactory,
        llm_control_panel: ChatAssistantControlPanel,
        extension_deep_research_commands: list,
        mcp_manager: "McpManager",
        model_info_string: str | None,
    ) -> Participants:
        execution_mode = ExecutionMode.get_from_cli_args(cli_args)
        user_participant = self._create_user_participant(cli_args, user_control_panel, execution_mode)
        assistant_participant = self._create_assistant_participant(
            cli_args, model_factory, llm_control_panel, extension_deep_research_commands, mcp_manager, model_info_string, execution_mode
        )
        return Participants(user=user_participant, assistant=assistant_participant)

    def print_welcome_message(self, model_info_string: str | None):
        self.notifications_printer.print_notification(
            textwrap.dedent(
                f"""
            Welcome to Hermes!

            Using model {model_info_string}
            """,
            ),
        )

    def _create_user_participant(
        self, cli_args: Namespace, user_control_panel: UserControlPanel, execution_mode: ExecutionMode
    ) -> UserParticipant:
        user_input_from_cli = user_control_panel.convert_cli_arguments_to_text(cli_args)
        stt_input_handler = self._create_stt_input_handler(cli_args)
        markdown_highlighter = None if cli_args.no_markdown else MarkdownHighlighter()

        user_control_panel.is_deep_research_mode = execution_mode == ExecutionMode.RESEARCH

        user_interface = UserOrchestrator(
            control_panel=user_control_panel,
            command_completer=CommandCompleter(user_control_panel.get_command_labels()),
            markdown_highlighter=markdown_highlighter,
            stt_input_handler=stt_input_handler,
            notifications_printer=self.notifications_printer,
            user_input_from_cli=user_input_from_cli,
        )
        return UserParticipant(user_interface)

    def _create_stt_input_handler(self, cli_args: Namespace) -> "STTInputHandler | None":
        if not cli_args.stt:
            return None

        from hermes.chat.interface.user.interface.stt_input_handler.stt_input_handler import STTInputHandler

        groq_api_key = self.config_manager.get_groq_api_key()
        if not groq_api_key:
            raise ValueError("Please set the GROQ api key in ~/.config/hermes/config.json")

        return STTInputHandler(api_key=groq_api_key)

    def _create_assistant_participant(
        self,
        cli_args: Namespace,
        model_factory: ModelFactory,
        llm_control_panel: ChatAssistantControlPanel,
        extension_deep_research_commands: list,
        mcp_manager: "McpManager",
        model_info_string: str | None,
        execution_mode: ExecutionMode,
    ):
        model_info_string = self._validate_model_info_string(model_info_string)

        provider, model_tag = model_info_string.split("/", 1)
        provider = provider.upper()

        model = model_factory.get_model(provider, model_tag, self.config_manager.get_config())

        if cli_args.debug:
            return self._create_debug_participant(model, llm_control_panel)
        if execution_mode == ExecutionMode.RESEARCH:
            return self._create_deep_research_participant(cli_args, model, extension_deep_research_commands, mcp_manager)
        return self._create_chat_participant(model, llm_control_panel, execution_mode == ExecutionMode.SIMPLE_AGENT)

    def _create_debug_participant(self, model, llm_control_panel) -> DebugParticipant:
        debug_interface = DebugInterface(control_panel=llm_control_panel, model=model)
        return DebugParticipant(debug_interface)

    def _create_deep_research_participant(
        self,
        cli_args,
        model,
        extension_deep_research_commands,
        mcp_manager: "McpManager",
    ) -> LLMParticipant:
        from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator

        provided_research_repo_argument = cli_args.research_repo
        if ":" in provided_research_repo_argument:
            research_repo_path, research_name = provided_research_repo_argument.split(":", 1)
        else:
            research_repo_path = provided_research_repo_argument
            research_name = None

        research_repo_path = Path(research_repo_path).absolute()

        deep_research_interface = DeepResearchAssistantOrchestrator(
            model=model,
            research_path=research_repo_path,
            extension_commands=extension_deep_research_commands,
            mcp_manager=mcp_manager,
            research_name=research_name,
        )
        self.notifications_printer.print_notification(
            f"Using Deep Research Assistant interface with research directory: {research_repo_path}",
        )
        return LLMParticipant(deep_research_interface)

    def _create_chat_participant(self, model, llm_control_panel, is_agent: bool) -> LLMParticipant:
        llm_interface = ChatAssistantOrchestrator(model, control_panel=llm_control_panel)
        if is_agent:
            llm_control_panel.enable_agent_mode()
        return LLMParticipant(llm_interface)

    def _validate_model_info_string(self, model_info_string: str | None) -> str:
        if not model_info_string:
            raise ValueError(
                "No model specified. Please specify a model using the --model argument or add a default model in the config "
                "file ~/.config/hermes/config.json.",
            )
        if "/" not in model_info_string:
            raise ValueError("Model info string should be in the format provider/model_tag")
        return model_info_string
