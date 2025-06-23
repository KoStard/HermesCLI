import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

# Use relative import within the same package
from .command import Command, CommandRegistry


@dataclass
class CommandError:
    """Represents an error encountered during command parsing or validation."""

    command_name: str | None  # Name of the command where error occurred
    message: str  # Description of the error
    line_number: int | None = None  # Line number where the error was detected
    is_syntax_error: bool = False  # True if it's a block syntax error (<<< >>>)


@dataclass
class ParseResult:
    """Result of parsing a single command block."""

    command_name: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    errors: list[CommandError] = field(default_factory=list)
    # Indicates if this specific block had a <<< >>> syntax error preventing parsing
    has_block_syntax_error: bool = False
    # Start line index (0-based) of the command block in the original text
    block_start_line_index: int | None = None


class CommandParser:
    """Parses text containing command blocks (<<< ... >>>) with sections (///...)."""

    def __init__(self, command_registry: CommandRegistry):
        # Use the provided instance of the registry
        self.registry = command_registry

    def parse_text(self, text: str) -> list[ParseResult]:
        """Parse all command blocks from the input text.

        Args:
            text: The raw text potentially containing command blocks.

        Returns:
            A list of ParseResult objects, one for each detected command block
            (even those with syntax errors). Includes results for syntax errors
            detected outside specific blocks (e.g., dangling tags).
        """
        results: list[ParseResult] = []
        lines = text.split("\n")

        # 1. Find potential command blocks and check overall block syntax
        potential_blocks, block_syntax_errors = self._find_blocks_and_check_syntax(lines)

        # Add block syntax errors as separate ParseResult entries
        for error in block_syntax_errors:
            results.append(ParseResult(errors=[error], has_block_syntax_error=True))

        # 2. Parse valid blocks
        for block_start_index, block_lines in potential_blocks:
            result = self._parse_single_block(block_start_index, block_lines)
            results.append(result)

        # Sort results by line number for predictable order
        results.sort(key=lambda r: r.block_start_line_index if r.block_start_line_index is not None else -1)

        return results

    def _find_blocks_and_check_syntax(self, lines: list[str]) -> tuple[list[tuple[int, list[str]]], list[CommandError]]:
        """Identifies potential command blocks (<<< ... >>>) and checks for syntax errors
        like mismatched or nested tags.

        Returns:
            A tuple containing:
            - A list of valid blocks: `[(start_line_index, block_lines), ...]`.
            - A list of `CommandError` objects for syntax issues.
        """
        blocks = []
        errors = []
        open_tag_index = self._process_lines_for_blocks_and_errors(lines, blocks, errors)

        # Check for unclosed blocks after processing all lines
        if open_tag_index is not None:
            errors.append(self._create_unclosed_block_error(open_tag_index))

        return blocks, errors

    def _process_lines_for_blocks_and_errors(
        self,
        lines: list[str],
        blocks: list[tuple[int, list[str]]],
        errors: list[CommandError],
    ) -> int | None:
        """Process lines to identify blocks and syntax errors."""
        open_tag_index: int | None = None

        for i, line in enumerate(lines):
            stripped_line = line.strip()
            open_tag_index = self._handle_line_tags(i, stripped_line, open_tag_index, lines, blocks, errors)

        return open_tag_index

    def _handle_line_tags(
        self,
        line_index: int,
        stripped_line: str,
        open_tag_index: int | None,
        lines: list[str],
        blocks: list[tuple[int, list[str]]],
        errors: list[CommandError],
    ) -> int | None:
        """Handle opening and closing tags for a single line."""
        if self._is_opening_tag(stripped_line):
            return self._handle_opening_tag(line_index, open_tag_index, errors)
        if self._is_closing_tag(stripped_line):
            return self._handle_closing_tag(line_index, open_tag_index, lines, blocks, errors)
        return open_tag_index

    def _handle_opening_tag(
        self,
        line_index: int,
        open_tag_index: int | None,
        errors: list[CommandError],
    ) -> int:
        """Handle an opening tag."""
        if open_tag_index is not None:
            errors.append(self._create_nested_tag_error(line_index))
        return line_index

    def _handle_closing_tag(
        self,
        line_index: int,
        open_tag_index: int | None,
        lines: list[str],
        blocks: list[tuple[int, list[str]]],
        errors: list[CommandError],
    ) -> int | None:
        """Handle a closing tag."""
        if open_tag_index is not None:
            blocks.append((open_tag_index, lines[open_tag_index : line_index + 1]))
            return None
        errors.append(self._create_unmatched_closing_tag_error(line_index))
        return open_tag_index

    def _is_opening_tag(self, line: str) -> bool:
        """Check if the line is an opening tag."""
        return bool(re.match(r"<<<\s*(\w+)", line))

    def _is_closing_tag(self, line: str) -> bool:
        """Check if the line is a closing tag."""
        return line == ">>>"

    def _create_nested_tag_error(self, line_index: int) -> CommandError:
        """Create an error for nested tags."""
        return CommandError(
            command_name=None,
            message="Found opening tag '<<<' before the previous one was closed with '>>>'.",
            line_number=line_index + 1,
            is_syntax_error=True,
        )

    def _create_unmatched_closing_tag_error(self, line_index: int) -> CommandError:
        """Create an error for unmatched closing tag."""
        return CommandError(
            command_name=None,
            message="Found closing tag '>>>' without a matching opening tag '<<<'.",
            line_number=line_index + 1,
            is_syntax_error=True,
        )

    def _create_unclosed_block_error(self, open_tag_index: int) -> CommandError:
        """Create an error for unclosed block."""
        return CommandError(
            command_name=None,
            message="Command block starting on this line was never closed with '>>>'.",
            line_number=open_tag_index + 1,
            is_syntax_error=True,
        )

    def _parse_single_block(self, block_start_index: int, block_lines: list[str]) -> ParseResult:
        """Parses the content of a single, syntactically valid command block."""
        result = ParseResult(block_start_line_index=block_start_index)
        opening_line = block_lines[0].strip()
        command_content_lines = block_lines[1:-1]
        command_content = "\n".join(command_content_lines)

        match = re.match(r"<<<\s*(\w+)", opening_line)
        if not match:  # Should not happen if _find_blocks_and_check_syntax is correct
            result.errors.append(
                CommandError(
                    None,
                    "Invalid block opening line format.",
                    block_start_index + 1,
                    True,
                ),
            )
            result.has_block_syntax_error = True
            return result

        command_name = match.group(1)
        result.command_name = command_name

        command = self.registry.get_command(command_name)
        if not command:
            result.errors.append(
                CommandError(
                    command_name=command_name,
                    message=f"Unknown command: '{command_name}'",
                    line_number=block_start_index + 1,
                ),
            )
            return result  # Cannot parse sections or validate if command is unknown

        # Parse sections (///section_name ...)
        args, section_errors = self._parse_command_sections(
            command_content,
            block_start_index + 1,  # Line number offset for content
            command,
        )
        result.errors.extend(section_errors)

        # Apply argument transformations (e.g., type conversion) defined in the command
        try:
            transformed_args = command.transform_args(args)
            result.args = transformed_args
        except Exception as e:
            result.errors.append(
                CommandError(
                    command_name=command_name,
                    message=f"Error during argument transformation: {e}",
                    line_number=block_start_index + 1,  # Error relates to the whole block
                ),
            )
            # Continue with original args for validation if transformation fails? Or stop?
            # Let's stop processing this command further if transform fails.
            return result

        # Validate arguments against command definition (required sections, etc.)
        # This uses the *transformed* args
        validation_errors = command.validate(result.args)
        for error_msg in validation_errors:
            result.errors.append(
                CommandError(
                    command_name=command_name,
                    message=error_msg,
                    line_number=block_start_index + 1,  # Validation error applies to the block
                ),
            )

        return result

    @staticmethod
    def _parse_command_sections(
        content: str,
        content_start_line: int,
        command: Command[Any, Any],
    ) -> tuple[dict[str, Any], list[CommandError]]:
        """Helper to parse ///section delimiters within command content.

        Args:
            content: The string content between <<< and >>>.
            content_start_line: The line number where the content starts.
            command: The Command instance being parsed.

        Returns:
            A tuple containing:
            - A dictionary of arguments: `{section_name: content_or_list_of_content}`.
            - A list of `CommandError` for section-related issues.
        """
        sections_found: dict[str, list[tuple[str, int]]] = defaultdict(list)
        errors: list[CommandError] = []
        last_pos = 0

        # Check content before first marker and collect section matches
        last_pos, errors = CommandParser._check_content_before_first_marker(
            content,
            content_start_line,
            command,
            errors,
        )

        # Find and process all section matches
        sections_found, last_pos, errors = CommandParser._process_section_matches(
            content,
            content_start_line,
            command,
            sections_found,
            errors,
        )

        # Check content after last marker
        sections_found, errors = CommandParser._check_content_after_last_marker(
            content,
            content_start_line,
            last_pos,
            command,
            sections_found,
            errors,
        )

        # Process collected sections according to command rules
        args = CommandParser._build_args_from_sections(command, sections_found, errors)

        return args, errors

    @staticmethod
    def _check_content_before_first_marker(
        content: str,
        content_start_line: int,
        command: Command[Any, Any],
        errors: list[CommandError],
    ) -> tuple[int, list[CommandError]]:
        """Check if there's any content before the first section marker."""
        first_marker_match = re.search(r"^\s*///", content, re.MULTILINE)
        if first_marker_match:
            content_before_first_marker = content[: first_marker_match.start()].strip()
            if content_before_first_marker:
                errors.append(
                    CommandError(
                        command_name=command.name,
                        message="Content found before the first '///section' marker.",
                        line_number=content_start_line,
                    ),
                )
            return first_marker_match.start(), errors
        return 0, errors

    @staticmethod
    def _process_section_matches(
        content: str,
        content_start_line: int,
        command: Command[Any, Any],
        sections_found: dict[str, list[tuple[str, int]]],
        errors: list[CommandError],
    ) -> tuple[dict[str, list[tuple[str, int]]], int, list[CommandError]]:
        """Process all section markers found in the content."""
        last_pos = 0
        section_matches = re.finditer(r"\s*///(\w+)\s*(.*?)(?=///|\Z)", content, re.MULTILINE | re.DOTALL)

        for match in section_matches:
            section_name = match.group(1)
            section_content = match.group(2).strip()
            line_num = content_start_line + content.count("\n", 0, match.start())
            last_pos = match.end()

            if section_name not in command.get_all_sections():
                errors.append(
                    CommandError(
                        command_name=command.name,
                        message=f"Unknown section '///{section_name}' for command '{command.name}'.",
                        line_number=line_num,
                    ),
                )
                continue

            if not section_content:
                errors.append(
                    CommandError(
                        command_name=command.name,
                        message=f"Section '///{section_name}' cannot be empty.",
                        line_number=line_num,
                    ),
                )
                continue

            sections_found[section_name].append((section_content, line_num))

        return sections_found, last_pos, errors

    @staticmethod
    def _check_content_after_last_marker(
        content: str,
        content_start_line: int,
        last_pos: int,
        command: Command[Any, Any],
        sections_found: dict[str, list[tuple[str, int]]],
        errors: list[CommandError],
    ) -> tuple[dict[str, list[tuple[str, int]]], list[CommandError]]:
        """Check if there's any content after the last section marker."""
        content_after_last_marker = content[last_pos:].strip()
        if not content_after_last_marker:
            return sections_found, errors

        sections = command.get_all_sections()
        line_num = content_start_line + content.count("\n", 0, last_pos)

        # If command has exactly one section and it's not found yet, treat trailing content as that section
        if len(sections) == 1 and not sections_found[sections[0]]:
            section_name = sections[0]
            sections_found[section_name].append((content_after_last_marker, line_num))
        else:
            errors.append(
                CommandError(
                    command_name=command.name,
                    message="Content found after the last '///section' marker.",
                    line_number=line_num,
                ),
            )

        return sections_found, errors

    @staticmethod
    def _build_args_from_sections(
        command: Command[Any, Any],
        sections_found: dict[str, list[tuple[str, int]]],
        errors: list[CommandError],
    ) -> dict[str, Any]:
        """Build the final arguments dictionary from collected sections."""
        args: dict[str, Any] = {}
        allow_multiple_dict = {section.name: section.allow_multiple for section in command.sections}

        for name, content_list in sections_found.items():
            allows_multiple = allow_multiple_dict.get(name, False)

            # Handle multiple sections when only one is allowed
            if len(content_list) > 1 and not allows_multiple:
                # Add errors for duplicates (skip the first one which is valid)
                for _, line_num in content_list[1:]:
                    errors.append(
                        CommandError(
                            command_name=command.name,
                            message=f"Multiple instances of section '///{name}' found, but only one is allowed.",
                            line_number=line_num,
                        ),
                    )
                # Only use the first instance
                args[name] = content_list[0][0]
            elif allows_multiple:
                # For sections allowing multiple instances, collect all content in a list
                args[name] = [content for content, _ in content_list]
            else:
                # For single-instance sections with just one value
                args[name] = content_list[0][0]

        return args

    @staticmethod
    def generate_error_report(parse_results: list[ParseResult]) -> str:
        """Generate a formatted error report string from a list of ParseResult objects.

        Args:
            parse_results: The list of results from `parse_text`.

        Returns:
            A formatted markdown string summarizing the errors, or an empty string
            if no errors were found.
        """
        all_errors = CommandParser._collect_and_sort_errors(parse_results)
        if not all_errors:
            return ""

        report_parts = ["### Command Parsing Errors Report:"]
        syntax_errors_found = False
        other_errors_found = False

        # Format each error and track error types
        for i, error in enumerate(all_errors, 1):
            error_lines, is_syntax_error = CommandParser._format_error(i, error)
            report_parts.extend(error_lines)

            if is_syntax_error:
                syntax_errors_found = True
            else:
                other_errors_found = True

        # Add footer notes
        footer_lines = CommandParser._generate_report_footer(syntax_errors_found, other_errors_found)
        report_parts.extend(footer_lines)

        return "\n".join(report_parts)

    @staticmethod
    def _collect_and_sort_errors(parse_results: list[ParseResult]) -> list[CommandError]:
        """Collect all errors from parse results and sort them by line number and message."""
        all_errors: list[CommandError] = []
        for result in parse_results:
            all_errors.extend(result.errors)

        # Sort errors primarily by line number, then by message
        all_errors.sort(
            key=lambda e: (
                e.line_number if e.line_number is not None else -1,
                e.message,
            ),
        )

        return all_errors

    @staticmethod
    def _format_error(index: int, error: CommandError) -> tuple[list[str], bool]:
        """Format a single error into report lines and indicate if it's a syntax error."""
        line_info = f" (near line {error.line_number})" if error.line_number else ""
        cmd_info = f" in command '{error.command_name}'" if error.command_name else ""

        error_type = "Syntax Error" if error.is_syntax_error else "Error"
        error_lines = [
            f"#### {error_type} {index}{line_info}{cmd_info}:",
            f"- {error.message}",
        ]

        return error_lines, error.is_syntax_error

    @staticmethod
    def _generate_report_footer(syntax_errors_found: bool, other_errors_found: bool) -> list[str]:
        """Generate footer notes based on the types of errors found."""
        footer_lines = ["---"]
        if syntax_errors_found:
            footer_lines.append("**Note:** Commands with block syntax errors (<<< \\n>>> issues) were not parsed or executed.")
        if other_errors_found:
            footer_lines.append(
                "**Note:** Commands with other errors (e.g., unknown command, missing/invalid sections) might be skipped during execution.",
            )

        return footer_lines
