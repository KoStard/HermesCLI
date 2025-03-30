import re
from typing import Dict, List, Tuple

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
        blocks, syntax_errors = self._check_block_command_syntax(text)
        if syntax_errors:
            # If there are syntax errors, return only those errors
            result = ParseResult()
            result.errors = syntax_errors
            result.has_syntax_error = True
            return [result]

        # Process the text line by line to identify block commands commands
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
            # TODO: Check that there are no more opening/closing symbols
            if line.startswith("<<<"):
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
                latest_opening_tag_index = index # Picking the latest, regardless duplicate or not
            elif line.startswith(">>>"):
                # There should have been an opening tag
                # If recent closing tag came after the latest opening tag, then we have duplicate closing tags
                if latest_closing_tag_index > latest_opening_tag_index:
                    # We have a problem
                    duplicate_closing_tag_indices.append(index)
                elif latest_opening_tag_index == -1:
                    unopened_closing_tag_indices.append(index)
                else:
                    # We are good
                    latest_closing_tag_index = index # Picking the earliest valid
                    blocks.append((latest_opening_tag_index, latest_closing_tag_index))
        
        # If there is a opening tag after the latest closing tag, then we have an open block left here
        if latest_opening_tag_index > latest_closing_tag_index:
            unclosed_opening_tag_indices.append(latest_opening_tag_index)
        
        for index in duplicate_opening_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="Duplicate opening tags. Other opening tags coming after it. This tag did not trigger a command.",
                    line_number=index,
                    is_syntax_error=True,
                )
            )
        
        for index in duplicate_closing_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="Duplicate closing tags. Other opening tags coming before it. This tag did not trigger a command.",
                    line_number=index,
                    is_syntax_error=True,
                )
            )
        
        for index in unclosed_opening_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="This command tag was never closed in the message. This tag did not trigger a command.",
                    line_number=index,
                    is_syntax_error=True,
                )
            )
        
        for index in unopened_closing_tag_indices:
            errors.append(
                CommandError(
                    command=lines[index],
                    message="This command tag does not have corresponding opening tag coming before it. This tag did not trigger a command.",
                    line_number=index,
                    is_syntax_error=True,
                )
            )

        return blocks, errors

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
