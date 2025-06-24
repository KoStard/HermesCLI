from collections.abc import Generator

from hermes.chat.events.base import Event
from hermes.chat.interface.assistant.chat.control_panel import ChatAssistantControlPanel
from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.user.control_panel.cli_adapter import CLIAdapter
from hermes.chat.interface.user.control_panel.exa_client import ExaClient
from hermes.chat.interface.user.control_panel.user_commands_executor import UserCommandsExecutor
from hermes.chat.interface.user.control_panel.user_commands_registry import UserCommandsRegistry
from hermes.chat.messages import Message
from hermes.utils.tree_generator import TreeGenerator


class UserControlPanel:
    def __init__(
        self,
        *,
        notifications_printer: CLINotificationsPrinter,
        extra_commands: list[ControlPanelCommand],
        exa_client: ExaClient,
        llm_control_panel: ChatAssistantControlPanel,
        is_deep_research_mode=False,
    ):
        self.tree_generator = TreeGenerator()
        self.llm_control_panel = llm_control_panel
        self.notifications_printer = notifications_printer
        self.exa_client = exa_client
        self.is_deep_research_mode = is_deep_research_mode

        # Initialize component classes
        self.commands_registry = UserCommandsRegistry(
            extra_commands=extra_commands,
        )

        self.commands_executor = UserCommandsExecutor(
            notifications_printer=notifications_printer,
            commands_registry=self.commands_registry,
            control_panel=self,
        )

        self.cli_adapter = CLIAdapter(
            notifications_printer=notifications_printer,
            commands_registry=self.commands_registry,
        )

    def render(self) -> str:
        """Render the available commands based on the current mode."""
        results = []
        for command_label in self.commands_registry.get_all_commands():
            command = self.commands_registry.get_command(command_label)
            if not command or not self._is_command_visible(command):
                continue
            results.append(self._render_command_in_control_panel(command_label))

        return "\n".join(results)

    def _is_command_visible(self, command: ControlPanelCommand) -> bool:
        """Determine if a command should be visible in the current mode."""
        is_agent_mode = self.llm_control_panel.is_agent_mode
        if not command.visible_from_interface:
            return False
        if self.is_deep_research_mode and not command.is_research_command:
            return False
        if is_agent_mode and not command.is_agent_command:
            return False
        if not is_agent_mode and not command.is_chat_command:  # noqa: SIM103
            return False
        return True

    def _render_command_in_control_panel(self, command_label: str) -> str:
        """Format a command for display in the control panel."""
        command = self.commands_registry.get_command(command_label)
        if not command:
            return ""
        return f"{command_label} - {command.description}"

    def extract_and_execute_commands(self, message: Message) -> Generator[Event, None, None]:
        """Extract commands from a message and execute them, yielding resulting events."""
        return self.commands_executor.extract_and_execute_commands(message)

    def get_command_labels(self) -> list[str]:
        """Get all command labels."""
        return self.commands_registry.get_all_commands()
