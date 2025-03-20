import re
from typing import Dict, List, Optional, Tuple

from .command import CommandError, CommandRegistry, ParseResult


class CommandParser:
    def __init__(self):
        self.registry = CommandRegistry()

    def parse_text(self, text: str) -> List[ParseResult]:
        """
        Parse all commands from text and return a list of parse results
        """
        results = []

        # First check for syntax errors in block commands
        syntax_errors = self._check_block_command_syntax(text)
        if syntax_errors:
            # If there are syntax errors, return only those errors
            result = ParseResult()
            result.errors = syntax_errors
            result.has_syntax_error = True
            return [result]

        # Process the text line by line to identify block commands and simple commands
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for block command start
            block_match = re.match(r"<<<\s*(\w+)", line)
            if block_match:
                command_name = block_match.group(1)
                block_content = []
                block_start_line = i
                i += 1

                # Collect all lines until the closing tag
                while i < len(lines) and not re.match(r">>>", lines[i].strip()):
                    block_content.append(lines[i])
                    i += 1

                # Check if we found the closing tag
                if i < len(lines) and re.match(r">>>", lines[i].strip()):
                    # Process the block command
                    result = ParseResult()
                    result.command_name = command_name

                    command = self.registry.get_command(command_name)
                    if command:
                        args, errors = self._parse_command_sections(
                            "\n".join(block_content),
                            block_start_line + 1,
                            command.get_required_sections(),
                            command_name,
                        )

                        # Apply any transformations to the arguments
                        args = command.transform_args(args)

                        # Validate the arguments
                        validation_errors = command.validate(args)
                        if validation_errors:
                            for error in validation_errors:
                                errors.append(
                                    CommandError(
                                        command=command_name,
                                        message=error,
                                        line_number=block_start_line + 1,
                                    )
                                )

                        result.args = args
                        result.errors = errors
                    else:
                        result.errors = [
                            CommandError(
                                command=command_name,
                                message=f"Unknown command: '{command_name}'",
                                line_number=block_start_line + 1,
                            )
                        ]

                    results.append(result)
                    i += 1  # Move past the closing tag
                else:
                    # Missing closing tag, but this should be caught by _check_block_command_syntax
                    i += 1

            else:
                i += 1

        return results

    def _check_block_command_syntax(self, text: str) -> List[CommandError]:
        """Check for syntax errors in block commands"""
        errors = []

        # Find all opening and closing tags with their line numbers
        lines = text.split("\n")
        opening_tags = []
        closing_tags = []

        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("<<<"):
                # Extract command name
                parts = line.split()
                command = parts[1] if len(parts) > 1 else "unknown"
                opening_tags.append((i + 1, command))
            elif line.startswith(">>>"):
                closing_tags.append(i + 1)

        # Check for unbalanced tags
        if len(opening_tags) > len(closing_tags):
            # Missing closing tags
            for i in range(len(closing_tags), len(opening_tags)):
                line_num, command = opening_tags[i]
                errors.append(
                    CommandError(
                        command=command,
                        message=f"Missing closing '>>>' tag for command block starting at line {line_num}",
                        line_number=line_num,
                        is_syntax_error=True,
                    )
                )
        elif len(closing_tags) > len(opening_tags):
            # Extra closing tags
            for i in range(len(opening_tags), len(closing_tags)):
                line_num = closing_tags[i]
                errors.append(
                    CommandError(
                        command="unknown",
                        message=f"Unexpected closing '>>>' tag without matching opening tag",
                        line_number=line_num,
                        is_syntax_error=True,
                    )
                )

        # Check for proper nesting (no overlapping blocks)
        if len(opening_tags) == len(closing_tags) and opening_tags:
            for i in range(len(opening_tags)):
                if (
                    i < len(opening_tags) - 1
                    and closing_tags[i] > opening_tags[i + 1][0]
                ):
                    line_num, command = opening_tags[i]
                    errors.append(
                        CommandError(
                            command=command,
                            message=f"Overlapping command blocks. Block starting at line {line_num} must be closed before starting a new block",
                            line_number=line_num,
                            is_syntax_error=True,
                        )
                    )

        return errors

    @staticmethod
    def _parse_command_sections(
        content: str, line_number: int, required_sections: List[str], command_name: str
    ) -> Tuple[Dict, List[CommandError]]:
        """Helper to parse command sections with /// delimiters"""
        errors = []
        result = {}

        # Find all sections in the content
        sections = re.findall(r"///(\w+)\s+(.*?)(?=///|\Z)", content, re.DOTALL)
        found_sections = {section[0]: section[1].strip() for section in sections}

        # Validate required sections
        for section in required_sections:
            if section not in found_sections:
                errors.append(
                    CommandError(
                        command=command_name,
                        message=f"Missing '///{section}' section in {command_name} command",
                        line_number=line_number,
                    )
                )
            elif not found_sections[section]:
                errors.append(
                    CommandError(
                        command=command_name,
                        message=f"{section.capitalize()} cannot be empty",
                        line_number=line_number,
                    )
                )

        # Add valid sections to result
        for section, value in found_sections.items():
            if value:  # Only add non-empty values
                result[section] = value

        return result, errors

    @staticmethod
    def generate_error_report(parse_results: List[ParseResult]) -> str:
        """Generate an error report from parse results"""
        all_errors = []
        for result in parse_results:
            all_errors.extend(result.errors)

        if not all_errors:
            return ""

        report = "### Errors report:\n"
        for i, error in enumerate(all_errors, 1):
            line_info = f" at line {error.line_number}" if error.line_number else ""
            report += f"#### Error {i}\n"
            report += f"Command: {error.command}{line_info}\n"
            report += f"Message: {error.message}\n\n"

        # Add information about which commands have syntax errors
        # Use a list of tuples with (command_name, line_number) to distinguish between multiple instances
        commands_with_syntax_errors = [
            (
                result.command_name,
                result.errors[0].line_number if result.errors else None,
            )
            for result in parse_results
            if result.has_syntax_error
        ]
        if commands_with_syntax_errors:
            report += "Commands with syntax errors that will not be executed:\n"
            for cmd, line_num in commands_with_syntax_errors:
                line_info = f" at line {line_num}" if line_num else ""
                report += f"- {cmd}{line_info}\n"
            report += "\nOther valid commands will still be executed.\n"

        return report
