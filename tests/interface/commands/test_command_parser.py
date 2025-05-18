import unittest
from typing import Any

from hermes.chat.interface.commands.command import Command, CommandRegistry
from hermes.chat.interface.commands.command_parser import (
    CommandError,
    CommandParser,
    ParseResult,
)


class DummyParserCommand(Command[str]):
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

    def execute(self, context: str, args: dict[str, Any]) -> None:
        pass

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        if "transform_sec" in args:
            args["transform_sec"] = args["transform_sec"].upper()
        return args

    def validate(self, args: dict[str, Any]) -> list[str]:
        errors = super().validate(args)
        if "optional_sec" in args and len(args["optional_sec"]) < 3:
            errors.append("Optional section must be at least 3 characters long")
        return errors


class FaultyTransformCommand(Command[str]):
    def __init__(self):
        super().__init__("faulty_cmd", "Command that fails transformation")
        self.add_section("section", required=True)

    def execute(self, context: str, args: dict[str, Any]) -> None:
        pass

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        # This will raise an exception during transformation
        raise ValueError("Transformation failed on purpose")

    def validate(self, args: dict[str, Any]) -> list[str]:
        return super().validate(args)


class CommandParserTest(unittest.TestCase):
    def setUp(self):
        self.registry = CommandRegistry()
        self.registry.clear()
        self.command = DummyParserCommand()
        self.registry.register(self.command)
        self.registry.register(FaultyTransformCommand())
        self.parser = CommandParser(self.registry)

    def test_parse_valid_command(self):
        """Test parsing a valid command block."""
        text = """
        <<< test_cmd
        ///required_sec
        This is required content.
        ///optional_sec
        Optional stuff.
        ///multi_sec
        First multi value.
        ///multi_sec
        Second multi value.
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertFalse(result.has_block_syntax_error)
        self.assertEqual(result.command_name, "test_cmd")
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.args["required_sec"], "This is required content.")
        self.assertEqual(result.args["optional_sec"], "Optional stuff.")
        self.assertEqual(result.args["multi_sec"], ["First multi value.", "Second multi value."])

    def test_parse_unknown_command(self):
        """Test parsing an unknown command."""
        text = """
        <<< unknown_cmd
        ///section
        Content
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.command_name, "unknown_cmd")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Unknown command", result.errors[0].message)

    def test_parse_missing_required_section(self):
        """Test parsing a command missing a required section."""
        text = """
        <<< test_cmd
        ///optional_sec
        Optional content
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.command_name, "test_cmd")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Missing required", result.errors[0].message)

    def test_parse_unknown_section(self):
        """Test parsing a command with an unknown section."""
        text = """
        <<< test_cmd
        ///required_sec
        Required content
        ///unknown_sec
        Unknown section content
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Unknown section", result.errors[0].message)

    def test_parse_empty_section(self):
        """Test parsing a command with an empty section."""
        text = """
        <<< test_cmd
        ///required_sec

        ///optional_sec
        Valid content
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        print(result.errors)
        self.assertEqual(len(result.errors), 2)
        self.assertIn("cannot be empty", result.errors[0].message)

    def test_parse_duplicate_non_multi_section(self):
        """Test parsing a command with a duplicated non-multiple section."""
        text = """
        <<< test_cmd
        ///required_sec
        Required content
        ///required_sec
        Duplicate required content
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Multiple instances", result.errors[0].message)
        # Should use the first instance in args
        self.assertEqual(result.args["required_sec"], "Required content")

    def test_transform_args_error(self):
        """Test error handling during argument transformation."""
        text = """
        <<< faulty_cmd
        ///section
        Content
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Error during argument transformation", result.errors[0].message)

    def test_block_syntax_errors(self):
        """Test detection of command block syntax errors."""
        text = """
        <<< unclosed_block
        Content without closing tag

        >>> closing_without_opening

        <<< nested_block
        <<< inner_block
        >>> inner_closing
        >>> outer_closing
        """
        results = self.parser.parse_text(text)
        # We should have at least 3 syntax errors:
        # 1. Unclosed block
        # 2. Closing tag without opening
        # 3. Nested opening tag
        syntax_errors = [r for r in results if any(e.is_syntax_error for e in r.errors)]
        self.assertGreaterEqual(len(syntax_errors), 3)

    def test_content_before_first_marker(self):
        """Test detection of content before the first section marker."""
        text = """
        <<< test_cmd
        Content before any section
        ///required_sec
        Required content
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Content found before the first", result.errors[0].message)

    def test_content_after_last_marker(self):
        """Test detection of content after the last section marker."""
        class MultiSectionCommand(Command[str]):
            def __init__(self):
                super().__init__("single_sec", "Command with a single section")
                self.add_section("content", required=True, help_text="Section")
                self.add_section("content2", required=True, help_text="Section")

            def execute(self, context: str, args: dict[str, Any]) -> None:
                pass

        self.registry.register(MultiSectionCommand())
        text = """
        <<< test_cmd
        Required content
        Content after last section
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(len(result.errors), 2)
        self.assertIn("Content found after the last", result.errors[0].message)

    def test_multiple_commands(self):
        """Test parsing multiple command blocks."""
        text = """
        <<< test_cmd
        ///required_sec
        First command
        >>>

        Some text in between

        <<< test_cmd
        ///required_sec
        Second command
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].args["required_sec"], "First command")
        self.assertEqual(results[1].args["required_sec"], "Second command")

    def test_single_section_command_without_marker(self):
        """Test parsing a command with one section defined but no section marker."""
        # Create a simple command with only one section
        class SingleSectionCommand(Command[str]):
            def __init__(self):
                super().__init__("single_sec", "Command with a single section")
                self.add_section("content", required=True, help_text="The only section")

            def execute(self, context: str, args: dict[str, Any]) -> None:
                pass

        self.registry.register(SingleSectionCommand())

        text = """
        <<< single_sec
        This content should be automatically assigned to the 'content' section
        without needing the content marker.
        >>>
        """
        results = self.parser.parse_text(text)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].errors, [])  # No errors expected
        self.assertIn("content", results[0].args)
        self.assertIn("automatically assigned", results[0].args["content"])

    def test_generate_error_report(self):
        """Test generating an error report from ParseResults."""
        # Create a parse result with errors
        result = ParseResult(
            command_name="test_cmd",
            errors=[
                CommandError("test_cmd", "Error message 1", 10, False),
                CommandError("test_cmd", "Error message 2", 20, True),
            ],
            has_block_syntax_error=True,
            block_start_line_index=5,
        )

        report = CommandParser.generate_error_report([result])
        self.assertIn("Command Parsing Errors Report:", report)
        self.assertIn("Error message 1", report)
        self.assertIn("Error message 2", report)
        self.assertIn("Syntax Error", report)
        self.assertIn("(near line 10)", report)
        self.assertIn("(near line 20)", report)
        self.assertIn("with block syntax errors", report)


if __name__ == "__main__":
    unittest.main()
