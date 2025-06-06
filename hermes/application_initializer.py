import configparser
import logging
import textwrap
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.chat_assistant.command_status_override import ChatAssistantCommandStatusOverride
from hermes.chat.interface.assistant.chat_assistant.control_panel import ChatAssistantControlPanel
from hermes.chat.interface.assistant.chat_assistant.interface import ChatAssistantInterface
from hermes.chat.interface.assistant.models.model_factory import ModelFactory
from hermes.chat.interface.debug.debug_interface import DebugInterface
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.user.control_panel.exa_client import ExaClient
from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel
from hermes.chat.interface.user.interface.command_completer.command_completer import CommandCompleter
from hermes.chat.interface.user.interface.markdown_highlighter import MarkdownHighlighter
from hermes.chat.interface.user.interface.user_interface import UserInterface
from hermes.chat.participants import DebugParticipant, LLMParticipant, UserParticipant
from hermes.components_container import CoreComponents, Participants
from hermes.extensions_loader import Extensions, ExtensionsLoader

if TYPE_CHECKING:
    from hermes.chat.interface.user.interface.stt_input_handler.stt_input_handler import STTInputHandler


class ApplicationInitializer:
    def __init__(self, config: configparser.ConfigParser, command_status_overrides: dict[str, ChatAssistantCommandStatusOverride]):
        self.config = config
        self.command_status_overrides = command_status_overrides
        self.notifications_printer = CLINotificationsPrinter()

    def get_core_components(self) -> CoreComponents:
        extensions = self._load_extensions()
        model_factory = self._create_model_factory()
        exa_client = self._create_exa_client()

        llm_control_panel = self._create_llm_control_panel(extensions.llm_commands, exa_client)
        user_control_panel = self._create_user_control_panel(extensions.user_commands, exa_client, llm_control_panel)

        return CoreComponents(
            model_factory=model_factory,
            user_control_panel=user_control_panel,
            llm_control_panel=llm_control_panel,
            extension_utils_builders=extensions.utils_builders,
            extension_deep_research_commands=extensions.deep_research_commands,
        )

    def _load_extensions(self) -> Extensions:
        return ExtensionsLoader().load_extensions()

    def _create_model_factory(self) -> ModelFactory:
        return ModelFactory(self.notifications_printer)

    def _create_exa_client(self) -> ExaClient:
        api_key = None
        if "EXA" in self.config and "api_key" in self.config["EXA"]:
            api_key = self.config["EXA"]["api_key"]
        return ExaClient(api_key)

    def _create_llm_control_panel(self, llm_commands, exa_client) -> ChatAssistantControlPanel:
        return ChatAssistantControlPanel(
            notifications_printer=self.notifications_printer,
            extra_commands=llm_commands,
            exa_client=exa_client,
            command_status_overrides=self.command_status_overrides,
        )

    def _create_user_control_panel(self, user_commands, exa_client, llm_control_panel) -> UserControlPanel:
        return UserControlPanel(
            notifications_printer=self.notifications_printer,
            extra_commands=user_commands,
            exa_client=exa_client,
            llm_control_panel=llm_control_panel,
        )

    def create_participants(
        self,
        cli_args: Namespace,
        user_control_panel: UserControlPanel,
        model_factory: ModelFactory,
        llm_control_panel: ChatAssistantControlPanel,
        extension_deep_research_commands: list,
        model_info_string: str | None,
    ) -> Participants:
        user_participant = self._create_user_participant(cli_args, user_control_panel)
        assistant_participant = self._create_assistant_participant(
            cli_args, model_factory, llm_control_panel, extension_deep_research_commands, model_info_string
        )
        return Participants(user=user_participant, assistant=assistant_participant)

    def _create_user_participant(self, cli_args: Namespace, user_control_panel: UserControlPanel) -> UserParticipant:
        user_input_from_cli = user_control_panel.convert_cli_arguments_to_text(None, cli_args)
        stt_input_handler = self._create_stt_input_handler(cli_args)
        markdown_highlighter = None if cli_args.no_markdown else MarkdownHighlighter()

        user_control_panel.is_deep_research_mode = bool(cli_args.research_repo)

        user_interface = UserInterface(
            control_panel=user_control_panel,
            command_completer=CommandCompleter(user_control_panel.get_command_labels()),
            markdown_highlighter=markdown_highlighter,
            stt_input_handler=stt_input_handler,
            notifications_printer=self.notifications_printer,
            user_input_from_cli=user_input_from_cli,
        )
        return UserParticipant(user_interface)

    def setup_logging(self, verbose: bool):
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
            logging.debug("Debug logging enabled")
        else:
            logging.basicConfig(level=logging.INFO)

    def print_welcome_message(self, model_info_string: str | None):
        self.notifications_printer.print_notification(
            textwrap.dedent(
                f"""
            Welcome to Hermes!

            Using model {model_info_string}
            """
            )
        )

    def _create_stt_input_handler(self, cli_args: Namespace) -> "STTInputHandler | None":
        if not cli_args.stt:
            return None

        from hermes.chat.interface.user.interface.stt_input_handler.stt_input_handler import STTInputHandler

        if "GROQ" not in self.config or "api_key" not in self.config["GROQ"]:
            raise ValueError("Please set the GROQ api key in ~/.config/hermes/config.ini")

        return STTInputHandler(api_key=self.config["GROQ"]["api_key"])

    def _create_assistant_participant(
        self,
        cli_args: Namespace,
        model_factory: ModelFactory,
        llm_control_panel: ChatAssistantControlPanel,
        extension_deep_research_commands: list,
        model_info_string: str | None,
    ):
        model_info_string = self._validate_model_info_string(model_info_string)

        provider, model_tag = model_info_string.split("/", 1)
        provider = provider.upper()

        model = model_factory.get_model(provider, model_tag, self.config)

        if cli_args.debug:
            return self._create_debug_participant(model, llm_control_panel)
        elif cli_args.research_repo:
            return self._create_deep_research_participant(cli_args, model, extension_deep_research_commands)
        else:
            return self._create_chat_participant(model, llm_control_panel)

    def _create_debug_participant(self, model, llm_control_panel) -> DebugParticipant:
        debug_interface = DebugInterface(control_panel=llm_control_panel, model=model)
        return DebugParticipant(debug_interface)

    def _create_deep_research_participant(self, cli_args, model, extension_deep_research_commands) -> LLMParticipant:
        from hermes.chat.interface.assistant.agent.deep_research.interface import DeepResearchAssistantInterface

        provided_research_repo_argument = cli_args.research_repo
        research_repo_path, research_name = provided_research_repo_argument.split(":", 1)

        research_repo_path = Path(research_repo_path).absolute()

        deep_research_interface = DeepResearchAssistantInterface(
            model=model,
            research_path=research_repo_path,
            extension_commands=extension_deep_research_commands,
            research_name=research_name,
        )
        self.notifications_printer.print_notification(
            f"Using Deep Research Assistant interface with research directory: {research_repo_path}"
        )
        return LLMParticipant(deep_research_interface)

    def _create_chat_participant(self, model, llm_control_panel) -> LLMParticipant:
        llm_interface = ChatAssistantInterface(model, control_panel=llm_control_panel)
        return LLMParticipant(llm_interface)

    def _validate_model_info_string(self, model_info_string: str | None) -> str:
        if not model_info_string:
            raise ValueError(
                "No model specified. Please specify a model using the --model argument or add a default model in the config "
                "file ~/.config/hermes/config.ini."
            )
        if "/" not in model_info_string:
            raise ValueError("Model info string should be in the format provider/model_tag")
        return model_info_string
