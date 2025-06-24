from argparse import ArgumentParser, Namespace

from hermes.chat.interface.control_panel import ControlPanelCommand
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.user.control_panel.user_commands_registry import UserCommandsRegistry


class CLIAdapter:
    def __init__(
        self,
        *,
        notifications_printer: CLINotificationsPrinter,
        commands_registry: UserCommandsRegistry,
    ):
        self.notifications_printer = notifications_printer
        self.commands_registry = commands_registry
        self._cli_arguments: set[str] = set()  # Track which arguments were added to CLI

    def build_cli_arguments_for_chat(self, parser: ArgumentParser) -> None:
        for command_label in self.commands_registry.get_all_commands():
            command = self.commands_registry.get_command(command_label)
            if not command or not command.visible_from_cli or not command.is_chat_command:
                continue
            self._add_command_to_cli_parser(command_label, command, parser, command.default_on_cli)

    def build_cli_arguments_for_simple_agent(self, parser: ArgumentParser) -> None:
        for command_label in self.commands_registry.get_all_commands():
            command = self.commands_registry.get_command(command_label)
            if not command or not command.visible_from_cli or not command.is_agent_command:
                continue
            self._add_command_to_cli_parser(command_label, command, parser, command.default_on_cli)

    def build_cli_arguments_for_research(self, parser: ArgumentParser) -> None:
        for command_label in self.commands_registry.get_all_commands():
            command = self.commands_registry.get_command(command_label)
            if not command or not command.visible_from_cli or not command.is_research_command:
                continue
            self._add_command_to_cli_parser(command_label, command, parser, command.default_on_cli)

    def _add_command_to_cli_parser(
        self, command_label: str, command: ControlPanelCommand, parser: ArgumentParser, is_default: bool
    ) -> None:
        if command.with_argument:
            if is_default:
                parser.add_argument(
                    command_label[1:],
                    type=str,
                    nargs="*",
                    help=command.description,
                )
                self._cli_arguments.add(command_label[1:])
            else:
                parser.add_argument(
                    "--" + command_label[1:],
                    type=str,
                    action="append",
                    help=command.description,
                )
                self._cli_arguments.add(command_label[1:])
        else:
            # Add flag-only arguments (no values)
            parser.add_argument(
                "--" + command_label[1:],
                action="store_true",
                help=command.description,
            )
            self._cli_arguments.add(command_label[1:])

    def convert_cli_arguments_to_text(self, args: Namespace) -> str:
        lines = []
        args_dict = vars(args)

        for arg, value in args_dict.items():
            # Skip arguments that are None or not registered
            if value is None or arg not in self._cli_arguments:
                continue

            # Handle different argument types
            if isinstance(value, bool):
                lines.extend(self._format_boolean_arg(arg, value))
            elif arg == "prompt":
                lines.extend(self._format_prompt_arg(value))
            else:
                lines.extend(self._format_standard_arg(arg, value))

        return "\n".join(lines)

    def _format_boolean_arg(self, arg: str, value: bool) -> list[str]:
        if value:
            return [f"/{arg}"]
        return []

    def _format_prompt_arg(self, values: list[str]) -> list[str]:
        return list(values)

    def _format_standard_arg(self, arg: str, values: list[str]) -> list[str]:
        return [f"/{arg} {v}" for v in values]
