import re
from typing import Dict, Optional, Tuple, Union


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

    def parse(self, text: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Parse a command from text"""
        # Check for simple commands first
        simple_match = re.search(r'///(?:\s*)(\w+)(?:\s+(.*))?', text)
        if simple_match:
            command = simple_match.group(1)
            args = simple_match.group(2) if simple_match.group(2) else ""
            
            if command in self.simple_commands:
                return command, self.simple_commands[command](args)
        
        # Check for block commands
        block_match = re.search(r'<<<<<\s+(\w+)(.*?)>>>>>', text, re.DOTALL)
        if block_match:
            command = block_match.group(1)
            content = block_match.group(2)
            
            if command in self.block_commands:
                return command, self._parse_block_command(command, content)
        
        return None, None
        
    def _parse_block_command(self, command: str, content: str) -> Optional[Dict]:
        """Parse a block command directly"""
        if command in self.block_commands:
            return self.block_commands[command](content)
        return None

    def _parse_add_criteria(self, args: str) -> Dict:
        """Parse add_criteria command"""
        return {"criteria": args.strip()}

    def _parse_mark_criteria_as_done(self, args: str) -> Dict:
        """Parse mark_criteria_as_done command"""
        try:
            index = int(args.strip()) - 1  # Convert to 0-based index
            return {"index": index}
        except ValueError:
            return {"error": f"Invalid criteria index: {args}"}

    def _parse_focus_down(self, args: str) -> Dict:
        """Parse focus_down command"""
        return {"title": args.strip()}

    def _parse_focus_up(self, args: str) -> Dict:
        """Parse focus_up command"""
        return {}

    def _parse_finish_task(self, args: str) -> Dict:
        """Parse finish_task command"""
        return {}

    def _parse_define_problem(self, content: str) -> Dict:
        """Parse define_problem command"""
        title_match = re.search(r'///title\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not title_match or not content_match:
            return {"error": "Missing title or content in define_problem command"}
        
        return {
            "title": title_match.group(1).strip(),
            "content": content_match.group(1).strip()
        }

    def _parse_add_subproblem(self, content: str) -> Dict:
        """Parse add_subproblem command"""
        title_match = re.search(r'///title\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not title_match or not content_match:
            return {"error": "Missing title or content in add_subproblem command"}
        
        return {
            "title": title_match.group(1).strip(),
            "content": content_match.group(1).strip()
        }

    def _parse_add_attachment(self, content: str) -> Dict:
        """Parse add_attachment command"""
        name_match = re.search(r'///name\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not name_match or not content_match:
            return {"error": "Missing name or content in add_attachment command"}
        
        return {
            "name": name_match.group(1).strip(),
            "content": content_match.group(1).strip()
        }

    def _parse_write_report(self, content: str) -> Dict:
        """Parse write_report command"""
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not content_match:
            return {"error": "Missing content in write_report command"}
        
        return {
            "content": content_match.group(1).strip()
        }

    def _parse_append_to_problem_definition(self, content: str) -> Dict:
        """Parse append_to_problem_definition command"""
        content_match = re.search(r'///content\s+(.*?)(?=///|\Z)', content, re.DOTALL)
        
        if not content_match:
            return {"error": "Missing content in append_to_problem_definition command"}
        
        return {
            "content": content_match.group(1).strip()
        }
