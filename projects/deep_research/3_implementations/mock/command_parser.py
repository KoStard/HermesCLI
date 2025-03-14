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
        self.simple_commands = {
            "add_criteria": self._parse_add_criteria,
            "mark_criteria_as_done": self._parse_mark_criteria_as_done,
            "focus_down": self._parse_focus_down,
            "focus_up": self._parse_focus_up,
            "finish_task": self._parse_finish_task,
        }
        
        self.block_commands = {
            "define_problem": self._parse_define_problem,
            "add_subproblem": self._parse_add_subproblem,
            "add_attachment": self._parse_add_attachment,
            "write_report": self._parse_write_report,
            "append_to_problem_definition": self._parse_append_to_problem_definition,
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
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for block command start
            block_match = re.match(r'<<<<<\s+(\w+)', line)
            if block_match:
                command = block_match.group(1)
                block_content = []
                block_start_line = i
                i += 1
                
                # Collect all lines until the closing tag
                while i < len(lines) and not re.match(r'>>>>>', lines[i].strip()):
                    block_content.append(lines[i])
                    i += 1
                
                # Check if we found the closing tag
                if i < len(lines) and re.match(r'>>>>>', lines[i].strip()):
                    # Process the block command
                    result = ParseResult()
                    result.command = command
                    
                    if command in self.block_commands:
                        args, errors = self.block_commands[command]('\n'.join(block_content), block_start_line + 1)
                        result.args = args
                        result.errors = errors
                    else:
                        result.errors = [CommandError(
                            command=command,
                            message=f"Unknown block command: '{command}'",
                            line_number=block_start_line + 1
                        )]
                    
                    results.append(result)
                    i += 1  # Move past the closing tag
                else:
                    # Missing closing tag, but this should be caught by _check_block_command_syntax
                    i += 1
            
            # Check for simple command
            elif line.startswith('///'):
                simple_match = re.match(r'///(?:\s*)(\w+)(?:\s+(.*))?', line)
                if simple_match:
                    command = simple_match.group(1)
                    args_text = simple_match.group(2) if simple_match.group(2) else ""
                    
                    # Skip simple commands that are inside block commands
                    # We check if this line is part of a section in a block command
                    if not any(cmd in command for cmd in ['title', 'content', 'name']):
                        result = ParseResult()
                        result.command = command
                        
                        if command in self.simple_commands:
                            args, errors = self.simple_commands[command](args_text, i + 1)
                            result.args = args
                            result.errors = errors
                        else:
                            result.errors = [CommandError(
                                command=command,
                                message=f"Unknown simple command: '{command}'",
                                line_number=i + 1
                            )]
                        
                        results.append(result)
                
                i += 1
            else:
                i += 1
        
        return results

    def _check_block_command_syntax(self, text: str) -> List[CommandError]:
        """Check for syntax errors in block commands"""
        errors = []
        
        # Find all opening and closing tags with their line numbers
        lines = text.split('\n')
        opening_tags = []
        closing_tags = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('<<<<<'):
                # Extract command name
                parts = line.split()
                command = parts[1] if len(parts) > 1 else "unknown"
                opening_tags.append((i + 1, command))
            elif line.startswith('>>>>>'):
                closing_tags.append(i + 1)
        
        # Check for unbalanced tags
        if len(opening_tags) > len(closing_tags):
            # Missing closing tags
            for i in range(len(closing_tags), len(opening_tags)):
                line_num, command = opening_tags[i]
                errors.append(CommandError(
                    command=command,
                    message=f"Missing closing '>>>>>' tag for command block starting at line {line_num}",
                    line_number=line_num,
                    is_syntax_error=True
                ))
        elif len(closing_tags) > len(opening_tags):
            # Extra closing tags
            for i in range(len(opening_tags), len(closing_tags)):
                line_num = closing_tags[i]
                errors.append(CommandError(
                    command="unknown",
                    message=f"Unexpected closing '>>>>>' tag without matching opening tag",
                    line_number=line_num,
                    is_syntax_error=True
                ))
        
        # Check for proper nesting (no overlapping blocks)
        if len(opening_tags) == len(closing_tags) and opening_tags:
            for i in range(len(opening_tags)):
                if i < len(opening_tags) - 1 and closing_tags[i] > opening_tags[i+1][0]:
                    line_num, command = opening_tags[i]
                    errors.append(CommandError(
                        command=command,
                        message=f"Overlapping command blocks. Block starting at line {line_num} must be closed before starting a new block",
                        line_number=line_num,
                        is_syntax_error=True
                    ))
        
        return errors


    def _parse_add_criteria(self, args: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse add_criteria command"""
        errors = []
        result = {}
        
        if not args.strip():
            errors.append(CommandError(
                command="add_criteria",
                message="Criteria text cannot be empty",
                line_number=line_number
            ))
        else:
            result["criteria"] = args.strip()
            
        return result, errors

    def _parse_mark_criteria_as_done(self, args: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse mark_criteria_as_done command"""
        errors = []
        result = {}
        
        try:
            index = int(args.strip()) - 1  # Convert to 0-based index
            if index < 0:
                errors.append(CommandError(
                    command="mark_criteria_as_done",
                    message=f"Criteria index must be positive, got: {index + 1}",
                    line_number=line_number
                ))
            else:
                result["index"] = index
        except ValueError:
            errors.append(CommandError(
                command="mark_criteria_as_done",
                message=f"Invalid criteria index: '{args.strip()}', must be a number",
                line_number=line_number
            ))
            
        return result, errors

    def _parse_focus_down(self, args: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse focus_down command"""
        errors = []
        result = {}
        
        if not args.strip():
            errors.append(CommandError(
                command="focus_down",
                message="Subproblem title cannot be empty",
                line_number=line_number
            ))
        else:
            result["title"] = args.strip()
            
        return result, errors

    def _parse_focus_up(self, args: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse focus_up command"""
        return {}, []

    def _parse_finish_task(self, args: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse finish_task command"""
        return {}, []

    def _parse_define_problem(self, content: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse define_problem command"""
        errors = []
        result = {}
        
        title_match = re.search(r'///title\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not title_match:
            errors.append(CommandError(
                command="define_problem",
                message="Missing '///title' section in define_problem command",
                line_number=line_number
            ))
        elif not title_match.group(1).strip():
            errors.append(CommandError(
                command="define_problem",
                message="Title cannot be empty",
                line_number=line_number + content[:title_match.start()].count('\n')
            ))
        else:
            result["title"] = title_match.group(1).strip()
        
        if not content_match:
            errors.append(CommandError(
                command="define_problem",
                message="Missing '///content' section in define_problem command",
                line_number=line_number
            ))
        elif not content_match.group(1).strip():
            errors.append(CommandError(
                command="define_problem",
                message="Content cannot be empty",
                line_number=line_number + content[:content_match.start()].count('\n')
            ))
        else:
            result["content"] = content_match.group(1).strip()
            
        return result, errors

    def _parse_add_subproblem(self, content: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse add_subproblem command"""
        errors = []
        result = {}
        
        title_match = re.search(r'///title\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not title_match:
            errors.append(CommandError(
                command="add_subproblem",
                message="Missing '///title' section in add_subproblem command",
                line_number=line_number
            ))
        elif not title_match.group(1).strip():
            errors.append(CommandError(
                command="add_subproblem",
                message="Title cannot be empty",
                line_number=line_number + content[:title_match.start()].count('\n')
            ))
        else:
            result["title"] = title_match.group(1).strip()
        
        if not content_match:
            errors.append(CommandError(
                command="add_subproblem",
                message="Missing '///content' section in add_subproblem command",
                line_number=line_number
            ))
        elif not content_match.group(1).strip():
            errors.append(CommandError(
                command="add_subproblem",
                message="Content cannot be empty",
                line_number=line_number + content[:content_match.start()].count('\n')
            ))
        else:
            result["content"] = content_match.group(1).strip()
            
        return result, errors

    def _parse_add_attachment(self, content: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse add_attachment command"""
        errors = []
        result = {}
        
        name_match = re.search(r'///name\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not name_match:
            errors.append(CommandError(
                command="add_attachment",
                message="Missing '///name' section in add_attachment command",
                line_number=line_number
            ))
        elif not name_match.group(1).strip():
            errors.append(CommandError(
                command="add_attachment",
                message="Name cannot be empty",
                line_number=line_number + content[:name_match.start()].count('\n')
            ))
        else:
            result["name"] = name_match.group(1).strip()
        
        if not content_match:
            errors.append(CommandError(
                command="add_attachment",
                message="Missing '///content' section in add_attachment command",
                line_number=line_number
            ))
        else:
            result["content"] = content_match.group(1).strip()
            
        return result, errors

    def _parse_write_report(self, content: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse write_report command"""
        errors = []
        result = {}
        
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not content_match:
            errors.append(CommandError(
                command="write_report",
                message="Missing '///content' section in write_report command",
                line_number=line_number
            ))
        elif not content_match.group(1).strip():
            errors.append(CommandError(
                command="write_report",
                message="Report content cannot be empty",
                line_number=line_number + content[:content_match.start()].count('\n')
            ))
        else:
            result["content"] = content_match.group(1).strip()
            
        return result, errors

    def _parse_append_to_problem_definition(self, content: str, line_number: int) -> Tuple[Dict, List[CommandError]]:
        """Parse append_to_problem_definition command"""
        errors = []
        result = {}
        
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not content_match:
            errors.append(CommandError(
                command="append_to_problem_definition",
                message="Missing '///content' section in append_to_problem_definition command",
                line_number=line_number
            ))
        elif not content_match.group(1).strip():
            errors.append(CommandError(
                command="append_to_problem_definition",
                message="Content cannot be empty",
                line_number=line_number + content[:content_match.start()].count('\n')
            ))
        else:
            result["content"] = content_match.group(1).strip()
            
        return result, errors
        
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
