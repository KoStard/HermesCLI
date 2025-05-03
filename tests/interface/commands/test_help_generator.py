import re
import unittest
from typing import Any

from hermes.interface.commands.command import Command, CommandRegistry
from hermes.interface.commands.help_generator import CommandHelpGenerator


# Test implementation of Command for help generator testing
class TestHelpCommand1(Command[str]):
    def __init__(self):
        super().__init__("cmd1", "First test command")
        self.add_section("title", required=True, help_text="The title section")
        self.add_section("body", required=True, help_text="The body content")
        self.add_section("tags", required=False, help_text="Optional tags", allow_multiple=True)

    def execute(self, context: str, args: dict[str, Any]) -> None:
        pass


class TestHelpCommand2(Command[str]):
    def __init__(self):
        super().__init__("cmd2", "Second test command with\nmultiple line\nhelp text")
        self.add_section("content", required=True, help_text="The main content")

    def execute(self, context: str, args: dict[str, Any]) -> None:
        pass


class CommandHelpGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.help_generator = CommandHelpGenerator()
        self.registry = CommandRegistry()
        self.registry.clear()

        # Register test commands
        self.cmd1 = TestHelpCommand1()
        self.cmd2 = TestHelpCommand2()
        self.registry.register(self.cmd1)
        self.registry.register(self.cmd2)

        # Get all commands for help generation
        self.commands = self.registry.get_all_commands()

    def test_help_generation(self):
        """Test generating help text for commands."""
        help_text = self.help_generator.generate_help(self.commands)

        # Verify help text contains both commands
        self.assertIn("<<< cmd1", help_text)
        self.assertIn("<<< cmd2", help_text)

        # Verify command sections are present
        self.assertIn("///title", help_text)
        self.assertIn("///body", help_text)
        self.assertIn("///tags (multiple allowed)", help_text)
        self.assertIn("///content", help_text)

        # Verify help text is included
        self.assertIn("The title section", help_text)
        self.assertIn("The body content", help_text)
        self.assertIn("Optional tags", help_text)

        # Verify command help text is properly formatted with semicolons
        self.assertIn("; First test command", help_text)
        self.assertIn("; Second test command with", help_text)
        self.assertIn("; multiple line", help_text)
        self.assertIn("; help text", help_text)

        # Check format validity - each command section should be properly formatted
        help_sections = re.split(r"<<< \w+", help_text)
        for section in help_sections[1:]:  # Skip the first empty split
            # Sections should end with >>> followed by semicolon help or blank line
            self.assertTrue(re.search(r">>>\s+(; .*|\s*\n)", section))

            # Section names should be prefixed with three slashes
            section_markers = re.findall(r"///\w+", section)
            self.assertGreater(len(section_markers), 0)

    def test_help_generation_empty_commands(self):
        """Test generating help text with no commands."""
        help_text = self.help_generator.generate_help({})
        # Should return an empty string or just whitespace
        self.assertEqual(help_text.strip(), "")


if __name__ == "__main__":
    unittest.main()
