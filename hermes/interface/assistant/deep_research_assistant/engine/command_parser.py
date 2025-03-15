import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union


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

    command: Optional[str] = None
    args: Dict = field(default_factory=dict)
    errors: List[CommandError] = field(default_factory=list)
    has_syntax_error: bool = False


class CommandParser:
    def __init__(self):
        self.block_commands = {
            "add_criteria": self._parse_add_criteria_block,
            "mark_criteria_as_done": self._parse_mark_criteria_as_done_block,
            "focus_down": self._parse_focus_down_block,
            "focus_up": self._parse_focus_up_block,
            "fail_task_and_focus_up": self._parse_focus_up_block,  # Use same parser as focus_up
            "define_problem": self._parse_define_problem,
            "add_subproblem": self._parse_add_subproblem,
            "add_attachment": self._parse_add_attachment,
            "write_report": self._parse_write_report,
            "append_to_problem_definition": self._parse_append_to_problem_definition,
            "add_criteria_to_subproblem": self._parse_add_criteria_to_subproblem,
        }

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
                command = block_match.group(1)
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
                    result.command = command

                    if command in self.block_commands:
                        args, errors = self.block_commands[command](
                            "\n".join(block_content), block_start_line + 1
                        )
                        result.args = args
                        result.errors = errors
                    else:
                        result.errors = [
                            CommandError(
                                command=command,
                                message=f"Unknown block command: '{command}'",
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

    def _parse_command_sections(
        self, 
        content: str,
        line_number: int,
        required_sections: List[str],
        command_name: str
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
                errors.append(CommandError(
                    command=command_name,
                    message=f"Missing '///{section}' section in {command_name} command",
                    line_number=line_number,
                ))
            elif not found_sections[section]:
                errors.append(CommandError(
                    command=command_name,
                    message=f"{section.capitalize()} cannot be empty",
                    line_number=line_number,
                ))
                
        # Add valid sections to result
        for section, value in found_sections.items():
            if value:  # Only add non-empty values
                result[section] = value
                
        return result, errors

    def _parse_add_criteria_block(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse add_criteria block command"""
        return self._parse_command_sections(
            content, line_number, ["criteria"], "add_criteria"
        )

    def _parse_mark_criteria_as_done_block(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse mark_criteria_as_done block command"""
        result, errors = self._parse_command_sections(
            content, line_number, ["criteria_number"], "mark_criteria_as_done"
        )
        
        if "criteria_number" in result:
            try:
                index = int(result["criteria_number"]) - 1  # Convert to 0-based index
                if index < 0:
                    errors.append(CommandError(
                        command="mark_criteria_as_done",
                        message=f"Criteria index must be positive, got: {index + 1}",
                        line_number=line_number,
                    ))
                else:
                    result["index"] = index
            except ValueError:
                errors.append(CommandError(
                    command="mark_criteria_as_done",
                    message=f"Invalid criteria index: '{result['criteria_number']}', must be a number",
                    line_number=line_number,
                ))
                
        return result, errors

    def _parse_focus_down_block(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse focus_down block command"""
        errors = []
        result = {}

        title_match = re.search(r"///title\s+(.*?)(?=///|\Z)", content, re.DOTALL)
        
        if not title_match:
            errors.append(
                CommandError(
                    command="focus_down",
                    message="Missing '///title' section in focus_down command",
                    line_number=line_number,
                )
            )
        elif not title_match.group(1).strip():
            errors.append(
                CommandError(
                    command="focus_down",
                    message="Subproblem title cannot be empty",
                    line_number=line_number + content[:title_match.start()].count("\n"),
                )
            )
        else:
            result["title"] = title_match.group(1).strip()

        return result, errors

    def _parse_focus_up_block(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse focus_up block command (no arguments needed)"""
        return {}, []

    def _parse_define_problem(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse define_problem command"""
        return self._parse_command_sections(
            content, line_number, ["title", "content"], "define_problem"
        )

    def _parse_add_subproblem(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse add_subproblem command"""
        return self._parse_command_sections(
            content, line_number, ["title", "content"], "add_subproblem"
        )

    def _parse_add_attachment(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse add_attachment command"""
        return self._parse_command_sections(
            content, line_number, ["name", "content"], "add_attachment"
        )

    def _parse_write_report(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse write_report command"""
        return self._parse_command_sections(
            content, line_number, ["content"], "write_report"
        )

    def _parse_append_to_problem_definition(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse append_to_problem_definition command"""
        return self._parse_command_sections(
            content, line_number, ["content"], "append_to_problem_definition"
        )

    def _parse_add_criteria_to_subproblem(
        self, content: str, line_number: int
    ) -> Tuple[Dict, List[CommandError]]:
        """Parse add_criteria_to_subproblem command"""
        return self._parse_command_sections(
            content, line_number, ["title", "criteria"], "add_criteria_to_subproblem"
        )

    def generate_error_report(self, parse_results: List[ParseResult]) -> str:
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

        # Add information about command execution status
        has_syntax_error = any(result.has_syntax_error for result in parse_results)
        if has_syntax_error:
            report += "Not executing any commands as there was a syntax issue.\n"

        return report
