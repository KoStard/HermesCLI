from pathlib import Path
from typing import Any

from hermes.chat.interface.commands.command import Command
from hermes.chat.interface.commands.help_generator import CommandHelpGenerator
from hermes.chat.interface.templates.template_manager import TemplateManager


class AssistantPromptFactory:
    """Responsible for rendering the textual interface of the assistant."""

    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.template_manager = TemplateManager(templates_dir)
        self.help_generator = CommandHelpGenerator()

    def build_for(self, commands: list[Command[Any, Any]], is_agent_mode: bool) -> str:
        commands_help = self._render_commands_help(commands)
        return self.template_manager.render_template("assistant_static.mako", commands_help=commands_help, is_agent_mode=is_agent_mode)

    def _render_commands_help(self, commands: list[Command[Any, Any]]) -> str:
        command_help_contents = []
        for command in commands:
            command_help_contents.append(self._render_command_help(command))
        return "\n\n".join(command_help_contents)

    def _render_command_help(self, command: Command) -> str:
        """Render help for a specific command."""
        return self.help_generator.generate_help({command.name: command})
