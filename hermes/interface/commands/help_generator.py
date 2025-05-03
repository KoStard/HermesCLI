from pathlib import Path
from typing import Any

from hermes.interface.templates.template_manager import TemplateManager

from .command import Command


class CommandHelpGenerator:
    """
    Generates help text for commands using Mako templates.

    This class provides a way to generate help documentation for commands
    in various formats. It uses the TemplateManager to render templates
    with command information.
    """

    def __init__(self):
        default_templates_dir = Path(__file__).parent / "templates"
        self.template_manager = TemplateManager(default_templates_dir)

    def generate_help(self, commands: dict[str, Command[Any]]) -> str:
        """
        Generate help text for given commands.

        Args:
            commands: Map of all commands

        Returns:
            Formatted help text as a string.
        """
        return self.template_manager.render_template("command_help.mako", commands=commands)
