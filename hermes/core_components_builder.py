import logging
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.chat.command_status_override import ChatAssistantCommandStatusOverride
from hermes.chat.interface.assistant.chat.control_panel import ChatAssistantControlPanel
from hermes.chat.interface.assistant.models.model_factory import ModelFactory
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.user.control_panel.exa_client import ExaClient
from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel
from hermes.components_container import CoreComponents
from hermes.extensions_loader import Extensions, ExtensionsLoader
from hermes.mcp.mcp_manager import McpManager

if TYPE_CHECKING:
    from hermes.config_manager import ConfigManager


class CoreComponentsBuilder:
    def __init__(self, config_manager: "ConfigManager", command_status_overrides: dict[str, ChatAssistantCommandStatusOverride]):
        self.config_manager = config_manager
        self.command_status_overrides = command_status_overrides
        self.notifications_printer = CLINotificationsPrinter()

    def build(self) -> CoreComponents:
        extensions = self._load_extensions()
        model_factory = self._create_model_factory()
        exa_client = self._create_exa_client()

        chat_mcp_servers = self.config_manager.get_mcp_chat_assistant_servers()
        deep_research_mcp_servers = self.config_manager.get_mcp_deep_research_servers()
        mcp_manager = McpManager(chat_mcp_servers, deep_research_mcp_servers, self.notifications_printer)
        mcp_manager.start_loading()

        llm_control_panel = self._create_llm_control_panel(extensions.llm_commands, exa_client, mcp_manager)
        user_control_panel = self._create_user_control_panel(extensions.user_commands, exa_client, llm_control_panel)

        return CoreComponents(
            model_factory=model_factory,
            user_control_panel=user_control_panel,
            llm_control_panel=llm_control_panel,
            extension_utils_builders=extensions.utils_builders,
            extension_deep_research_commands=extensions.deep_research_commands,
            mcp_manager=mcp_manager,
        )

    def setup_logging(self, verbose: bool):
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
            logging.debug("Debug logging enabled")
        else:
            logging.basicConfig(level=logging.INFO)

    def _load_extensions(self) -> Extensions:
        return ExtensionsLoader().load_extensions()

    def _create_model_factory(self) -> ModelFactory:
        return ModelFactory(self.notifications_printer)

    def _create_exa_client(self) -> ExaClient:
        api_key = self.config_manager.get_exa_api_key()
        return ExaClient(api_key)

    def _create_llm_control_panel(self, llm_commands, exa_client, mcp_manager: McpManager) -> ChatAssistantControlPanel:
        return ChatAssistantControlPanel(
            notifications_printer=self.notifications_printer,
            extra_commands=llm_commands,
            exa_client=exa_client,
            command_status_overrides=self.command_status_overrides,
            mcp_manager=mcp_manager,
        )

    def _create_user_control_panel(self, user_commands, exa_client, llm_control_panel) -> UserControlPanel:
        return UserControlPanel(
            notifications_printer=self.notifications_printer,
            extra_commands=user_commands,
            exa_client=exa_client,
            llm_control_panel=llm_control_panel,
        )
