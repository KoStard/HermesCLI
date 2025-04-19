import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .command import CommandRegistry, Command


@dataclass
class CommandError:
    """Represents an error in command parsing"""

    command: str
    message: str
    line_number: Optional[int] = None
    is_syntax_error: bool = False


@dataclass
class ParseResult:
    """Result of parsing a command"""

    command_name: Optional[str] = None
    args: Dict[str, Any] = None
    errors: List[CommandError] = None
    has_syntax_error: bool = False

    def __post_init__(self):
        if self.args is None:
            self.args = {}
        if self.errors is None:
            self.errors = []


class CommandParser:
    def __init__(self):
        self.registry = CommandRegistry()

    def parse_text(self, text: str) -> List[ParseResult]:
        """
        Parse all commands from text and return a list of parse results
        """
        results = []

        # First check for syntax errors in block commands
        blocks, syntax_errors = self._check_block_command_syntax(text)
        if syntax_errors:
            # TODO: Find a better way to represent syntax errors
            result = ParseResult()
            result.errors = syntax_errors
            result.has_syntax_error = True
            results.append(result)

        for block in blocks:
            block_start_line_index = block[0]
            block_lines = block[1]
            opening_line = block_lines[0].strip()
            command_content = block_lines[1:-1]
            block_match = re.match(r"<<<\s*(\w+)", opening_line)
            command_name = block_match.group(1)
            
            result = ParseResult()
            result.command_name = command_name
            
            command = self.registry.get_command(command_name)
            if command:
                args, errors = self._parse_command_sections(
                    "\n".join(command_content),
                    block_start_line_index + 1,
                    command,
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
                                line_number=block_start_line_index + 1,
                            )
                        )

                result.args = args
                result.errors = errors
            else:
                result.errors = [
                    CommandError(
                        command=command_name,
                        message=f"Unknown command: '{command_name}'",
                        line_number=block_start_line_index + 1,
                    )
                ]
            
            results.append(result)
        
        return results

    def _check_block_command_syntax(self, text: str) -> Tuple[Tuple[int, List[str]], List[CommandError]]:
        """Check for syntax errors in block commands"""
        # TODO: This method should return not just errors, but the blocks that will be processed
        # Otherwise we'll have duplicate logic
        errors = []

        lines = text.split("\n")
        latest_opening_tag_index = -1
        latest_closing_tag_index = -1
        blocks = []
        duplicate_opening_tag_indices = []
        duplicate_closing_tag_indices = []
        unclosed_opening_tag_indices = []
        unopened_closing_tag_indices = []

        for index, line in enumerate(lines):
            line = line.strip()
            if re.match(r"<<<\s*(\w+)", line):
                # There should have been a closing tag or nothing
                # So latest_closing_tag > latest_opening_tag
                # Otherwise multiple opening tags
                if latest_opening_tag_index > latest_closing_tag_index:
                    # We have a problem
                    # Considering the previous opening one as problematic
                    duplicate_opening_tag_indices.append(latest_opening_tag_index)
                else:
                    # We are good
                    pass
                latest_opening_tag_index = (
                    index  # Picking the latest, regardless duplicate or not
                )
            elif line == ">>>":
                # There should have been an opening tag
                # If recent closing tag came after the latest opening tag, then we have duplicate closing tags
                if latest_closing_tag_index > latest_opening_tag_index:
                    # We have a problem
                    duplicate_closing_tag_indices.append(index)
                elif latest_opening_tag_index == -1:
                    unopened_closing_tag_indices.append(index)
                else:
                    # We are good
                    latest_closing_tag_index = index  # Picking the earliest valid
                    blocks.append((latest_opening_tag_index, lines[latest_opening_tag_index:latest_closing_tag_index+1]))

        # If there is a opening tag after the latest closing tag, then we have an open block left here
        if latest_opening_tag_index > latest_closing_tag_index:
            unclosed_opening_tag_indices.append(latest_opening_tag_index)

        for index in duplicate_opening_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="Duplicate opening tags. Other opening tags coming after it. This tag did not trigger a command.",
                    line_number=index + 1,
                    is_syntax_error=True,
                )
            )

        for index in duplicate_closing_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="Duplicate closing tags. Other opening tags coming before it. This tag did not trigger a command.",
                    line_number=index + 1,
                    is_syntax_error=True,
                )
            )

        for index in unclosed_opening_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="This command tag was never closed in the message. This tag did not trigger a command.",
                    line_number=index + 1,
                    is_syntax_error=True,
                )
            )

        for index in unopened_closing_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="This command tag does not have corresponding opening tag coming before it. This tag did not trigger a command.",
                    line_number=index + 1,
                    is_syntax_error=True,
                )
            )

        return blocks, errors

    @staticmethod
    def _parse_command_sections(
        content: str, line_number: int, command: Command, command_name: str
    ) -> Tuple[Dict, List[CommandError]]:
        """Helper to parse command sections with /// delimiters"""
        required_sections = command.get_required_sections()
        errors = []
        arguments = {}

        # Find all sections in the content
        sections = re.findall(r"///(\w+)\s+(.*?)(?=///|\Z)", content, re.DOTALL)
        
        # Track sections that allow multiple instances
        sections_by_name = defaultdict(list)
        for section_name, section_content in sections:
            sections_by_name[section_name].append(section_content.strip())

        allow_multiple_dict = {
            section.name: section.allow_multiple
            for section in command.sections
        }
            
        # Validate required sections
        for section in required_sections:
            if section not in sections_by_name:
                errors.append(
                    CommandError(
                        command=command_name,
                        message=f"Missing '///{section}' section in {command_name} command",
                        line_number=line_number,
                    )
                )
            elif not sections_by_name[section] or not any(sections_by_name[section]):
                errors.append(
                    CommandError(
                        command=command_name,
                        message=f"{section.capitalize()} cannot be empty",
                        line_number=line_number,
                    )
                )
        
        # Validate that sections that don't allow multiple instances don't have multiple values
        for section_name, values in sections_by_name.items():
            if len(values) > 1 and not allow_multiple_dict.get(section_name, False):
                errors.append(
                    CommandError(
                        command=command_name,
                        message=f"Multiple instances of section '{section_name}' provided, but this section doesn't allow multiple instances",
                        line_number=line_number,
                    )
                )

        # Process sections with their values
        for section_name, values in sections_by_name.items():
            # Filter out empty values
            valid_values = [v for v in values if v]
            if not valid_values:
                continue
                
            if allow_multiple_dict.get(section_name, False):
                arguments[section_name] = valid_values
            else:
                arguments[section_name] = valid_values[0]

        return arguments, errors

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

        report += "Commands with syntax errors that will not be executed.\n"
        report += "Other valid commands will still be executed.\n"

        return report


if __name__ == '__main__':
    print(CommandParser().parse_text(
"""
<<< wiki_search
<<< query
confirm focused strategy high impact prioritize single strategy explain reasoning succinct
"""
))
