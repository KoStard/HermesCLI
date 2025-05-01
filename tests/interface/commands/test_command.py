import unittest
from typing import Any, Dict, List
from hermes.interface.commands.command import Command, CommandSection, CommandRegistry


# Test implementation of Command for testing
class TestCommand(Command[str]):  # Using str as a simple context type for testing
    def __init__(self):
        super().__init__("test_cmd", "Test command help text")
        self.add_section("required_sec", required=True, help_text="Required section")
        self.add_section("optional_sec", required=False, help_text="Optional section")
        self.add_section(
            "multi_sec",
            required=False,
            help_text="Multiple section",
            allow_multiple=True,
        )
        self.executed = False
        self.execution_args = None
        self.execution_context = None

    def execute(self, context: str, args: Dict[str, Any]) -> None:
        self.executed = True
        self.execution_context = context
        self.execution_args = args

    def transform_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        if "optional_sec" in args:
            args["optional_sec"] = args["optional_sec"].upper()
        return args

    def validate(self, args: Dict[str, Any]) -> List[str]:
        errors = super().validate(args)
        if "optional_sec" in args and len(args["optional_sec"]) < 3:
            errors.append("Optional section must be at least 3 characters long")
        return errors


class CommandTest(unittest.TestCase):
    def setUp(self):
        self.command = TestCommand()

    def test_command_initialization(self):
        """Test that a command is properly initialized with name and help text."""
        self.assertEqual(self.command.name, "test_cmd")
        self.assertEqual(self.command.help_text, "Test command help text")
        self.assertEqual(len(self.command.sections), 3)

    def test_add_section(self):
        """Test adding sections to a command."""
        self.command.add_section("new_sec", required=True, help_text="New section")
        self.assertEqual(len(self.command.sections), 4)
        new_section = next(
            (s for s in self.command.sections if s.name == "new_sec"), None
        )
        self.assertIsNotNone(new_section)
        self.assertTrue(new_section.required)
        self.assertEqual(new_section.help_text, "New section")
        self.assertFalse(new_section.allow_multiple)

    def test_get_required_sections(self):
        """Test retrieving required sections."""
        required_sections = self.command.get_required_sections()
        self.assertIn("required_sec", required_sections)
        self.assertNotIn("optional_sec", required_sections)
        self.assertNotIn("multi_sec", required_sections)

    def test_get_all_sections(self):
        """Test retrieving all sections."""
        all_sections = self.command.get_all_sections()
        self.assertIn("required_sec", all_sections)
        self.assertIn("optional_sec", all_sections)
        self.assertIn("multi_sec", all_sections)
        self.assertEqual(len(all_sections), 3)

    def test_get_section_help(self):
        """Test retrieving help text for sections."""
        self.assertEqual(
            self.command.get_section_help("required_sec"), "Required section"
        )
        self.assertEqual(
            self.command.get_section_help("optional_sec"), "Optional section"
        )
        self.assertEqual(self.command.get_section_help("non_existent"), "")

    def test_validate(self):
        """Test command argument validation."""
        # Missing required section
        errors = self.command.validate({})
        self.assertEqual(len(errors), 1)
        self.assertIn("required_sec", errors[0])

        # All required sections provided
        errors = self.command.validate({"required_sec": "content"})
        self.assertEqual(len(errors), 0)

        # Custom validation
        errors = self.command.validate(
            {"required_sec": "content", "optional_sec": "ab"}
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("at least 3 characters", errors[0])

    def test_transform_args(self):
        """Test argument transformation."""
        args = {"required_sec": "required", "optional_sec": "make me upper"}
        transformed = self.command.transform_args(args)
        self.assertEqual(transformed["optional_sec"], "MAKE ME UPPER")
        self.assertEqual(transformed["required_sec"], "required")  # Unchanged

    def test_execute(self):
        """Test command execution."""
        context = "test context"
        args = {"required_sec": "content"}
        self.command.execute(context, args)
        self.assertTrue(self.command.executed)
        self.assertEqual(self.command.execution_context, context)
        self.assertEqual(self.command.execution_args, args)

    def test_should_be_last_in_message(self):
        """Test that by default commands are not marked as last in message."""
        self.assertFalse(self.command.should_be_last_in_message())


class CommandSectionTest(unittest.TestCase):
    def test_section_initialization(self):
        """Test that a command section is properly initialized."""
        section = CommandSection(
            "test", required=True, help_text="Test help", allow_multiple=True
        )
        self.assertEqual(section.name, "test")
        self.assertTrue(section.required)
        self.assertEqual(section.help_text, "Test help")
        self.assertTrue(section.allow_multiple)

        # Test default values
        default_section = CommandSection("default")
        self.assertEqual(default_section.name, "default")
        self.assertTrue(default_section.required)
        self.assertEqual(default_section.help_text, "")
        self.assertFalse(default_section.allow_multiple)


class CommandRegistryTest(unittest.TestCase):
    def setUp(self):
        self.registry = CommandRegistry()
        self.registry.clear()  # Ensure it's empty for testing

    def test_registry_singleton(self):
        """Test that CommandRegistry is a singleton."""
        registry1 = CommandRegistry()
        registry2 = CommandRegistry()
        self.assertIs(registry1, registry2)

    def test_register_and_get_command(self):
        """Test registering and retrieving commands."""
        command = TestCommand()
        self.registry.register(command)

        retrieved = self.registry.get_command("test_cmd")
        self.assertIs(retrieved, command)

        unknown = self.registry.get_command("unknown")
        self.assertIsNone(unknown)

    def test_get_all_commands(self):
        """Test retrieving all registered commands."""
        command1 = TestCommand()
        command1.name = "cmd1"
        command2 = TestCommand()
        command2.name = "cmd2"

        self.registry.register(command1)
        self.registry.register(command2)

        all_commands = self.registry.get_all_commands()
        self.assertEqual(len(all_commands), 2)
        self.assertIn("cmd1", all_commands)
        self.assertIn("cmd2", all_commands)
        # Verify it returns a copy
        all_commands["new_key"] = "value"
        self.assertNotIn("new_key", self.registry.get_all_commands())

    def test_get_command_names(self):
        """Test retrieving names of all registered commands."""
        command1 = TestCommand()
        command1.name = "cmd1"
        command2 = TestCommand()
        command2.name = "cmd2"

        self.registry.register(command1)
        self.registry.register(command2)

        names = self.registry.get_command_names()
        self.assertEqual(len(names), 2)
        self.assertIn("cmd1", names)
        self.assertIn("cmd2", names)

    def test_clear(self):
        """Test clearing the registry."""
        command = TestCommand()
        self.registry.register(command)
        self.assertEqual(len(self.registry.get_all_commands()), 1)

        self.registry.clear()
        self.assertEqual(len(self.registry.get_all_commands()), 0)


if __name__ == "__main__":
    unittest.main()
