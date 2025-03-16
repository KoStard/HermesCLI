import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .command_parser import CommandParser, ParseResult
from .file_system import FileSystem
from .history import ChatHistory
from .interface import DeepResearcherInterface
from .logger import DeepResearchLogger


class DeepResearchEngine:
    """Core engine for Deep Research functionality, independent of UI implementation"""
    
    def __init__(
        self,
        instruction: str,
        initial_attachments: List[str] = None,
        root_dir: str = "research",
    ):
        self.file_system = FileSystem(root_dir)
        self.chat_history = ChatHistory()
        self.interface = DeepResearcherInterface(self.file_system, instruction)
        self.command_parser = CommandParser()
        self.initial_attachments = initial_attachments or []
        self.finished = False
        self.logger = DeepResearchLogger(Path(root_dir))

        # Check if problem already exists
        existing_problem = self.file_system.load_existing_problem()
        self.problem_defined = existing_problem is not None
        
        # Print initial status
        self._print_current_status()
    
    def get_interface_content(self) -> str:
        """Get the current interface content as a string"""
        if not self.problem_defined:
            return self.interface.render_no_problem_defined(self.initial_attachments)
        else:
            return self.interface.render_problem_defined()
    
    def process_commands(self, text: str) -> tuple[bool, str, Dict]:
        """
        Process commands from text
        
        Returns:
            tuple: (commands_executed, error_report, execution_status)
        """
        # Check for emergency shutdown code
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            self.finished = True
            return True, "System shutdown requested and executed.", {"shutdown": "success"}
            
        # Add the assistant's message to history
        self.chat_history.add_message("assistant", text)

        # Parse all commands from the text
        parse_results = self.command_parser.parse_text(text)

        # Check for errors
        has_errors = any(result.errors for result in parse_results)
        has_syntax_error = any(result.has_syntax_error for result in parse_results)

        # Track execution status for reporting
        execution_status = {}

        # Generate error report if there are errors
        error_report = ""
        if has_errors:
            error_report = self.command_parser.generate_error_report(parse_results)

        # If there are syntax errors, don't execute any commands
        if has_syntax_error:
            auto_reply = f'Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done.\n\n{error_report}'
            self.chat_history.add_message("user", auto_reply)
            print(auto_reply)
            return False, error_report, execution_status

        # Execute commands if there are no syntax errors
        commands_executed = False

        for result in parse_results:
            if result.command and not result.errors:
                try:
                    self._execute_command(result.command, result.args)
                    execution_status[result.command] = "success"
                    commands_executed = True
                except ValueError as e:
                    execution_status[result.command] = f"failed: {str(e)}"

        # Add execution status to error report if there were failures
        if any(status.startswith("failed") for status in execution_status.values()):
            if not error_report:
                error_report = "### Execution Status Report:\n"
            else:
                error_report += "\n### Execution Status Report:\n"

            for cmd, status in execution_status.items():
                if status.startswith("failed"):
                    error_report += f"- Command '{cmd}' {status}\n"

        # If no commands were executed
        if not commands_executed:
            auto_reply = f'Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done.'
            if error_report:
                auto_reply += f"\n\n{error_report}"
            self.chat_history.add_message("user", auto_reply)
            print(auto_reply)
        
        self._print_current_status()
        return commands_executed, error_report, execution_status

    def _execute_command(self, command: str, args: dict):
        """Execute a command"""
        if not self.problem_defined:
            if command == "define_problem":
                self._handle_define_problem(args)
            else:
                # This error will be captured in the error report
                pass
            return

        # Commands available when problem is defined
        command_handlers = {
            "add_criteria": self._handle_add_criteria,
            "mark_criteria_as_done": self._handle_mark_criteria_as_done,
            "add_subproblem": self._handle_add_subproblem,
            "add_attachment": self._handle_add_attachment,
            "write_report": self._handle_write_report,
            "append_to_problem_definition": self._handle_append_to_problem_definition,
            "add_criteria_to_subproblem": self._handle_add_criteria_to_subproblem,
            "focus_down": self._handle_focus_down,
            "focus_up": self._handle_focus_up,
            "fail_problem_and_focus_up": self._handle_fail_problem_and_focus_up,
        }

        if command in command_handlers:
            command_handlers[command](args)
        else:
            # This error will be captured in the error report
            pass

    def _handle_define_problem(self, args: dict):
        """Handle define_problem command"""
        self.file_system.create_root_problem(args["title"], args["content"])

        # Copy initial attachments to the root problem
        for attachment in self.initial_attachments:
            self.file_system.current_node.add_attachment(
                attachment, f"Content of {attachment} would be here..."
            )

        # Ensure file system is fully updated
        self.file_system.update_files()

        # Clear history as we're starting fresh with a defined problem
        self.chat_history.clear()

        self.problem_defined = True
        
        # Print status after problem definition
        self._print_current_status()

    def _handle_add_criteria(self, args: dict):
        """Handle add_criteria command"""
        if not self.file_system.current_node:
            return

        # Check if criteria already exists (per requirements in 3 - commands.md)
        criteria_text = args["criteria"]
        if criteria_text in self.file_system.current_node.criteria:
            return

        index = self.file_system.current_node.add_criteria(criteria_text)
        self.file_system.update_files()

    def _handle_mark_criteria_as_done(self, args: dict):
        """Handle mark_criteria_as_done command"""
        if not self.file_system.current_node:
            return

        success = self.file_system.current_node.mark_criteria_as_done(args["index"])
        if success:
            self.file_system.update_files()

    def _handle_add_subproblem(self, args: dict):
        """Handle add_subproblem command"""
        if not self.file_system.current_node:
            return

        # Check if subproblem with this title already exists
        title = args["title"]
        if title in self.file_system.current_node.subproblems:
            return

        subproblem = self.file_system.current_node.add_subproblem(
            title, args["content"]
        )
        # Create directories for the new subproblem
        self.file_system._create_node_directories(subproblem)
        self.file_system.update_files()

    def _handle_add_attachment(self, args: dict):
        """Handle add_attachment command"""
        if not self.file_system.current_node:
            return

        self.file_system.current_node.add_attachment(args["name"], args["content"])
        self.file_system.update_files()

    def _handle_write_report(self, args: dict):
        """Handle write_report command"""
        if not self.file_system.current_node:
            return

        self.file_system.current_node.write_report(args["content"])
        self.file_system.update_files()

    def _handle_append_to_problem_definition(self, args: dict):
        """Handle append_to_problem_definition command"""
        if not self.file_system.current_node:
            return

        self.file_system.current_node.append_to_problem_definition(args["content"])
        self.file_system.update_files()

    def _handle_focus_down(self, args: dict):
        """Handle focus_down command"""
        if not self.file_system.current_node:
            return

        result = self.file_system.focus_down(args["title"])
        if result:
            # Clear history when changing focus
            self.chat_history.clear()
            
            # Print updated status after focus change
            self._print_current_status()

    def _handle_focus_up(self, args: dict):
        """Handle focus_up command"""
        if (
            not self.file_system.current_node
        ):
            return

        # Check if report is written before allowing focus_up
        if not self.file_system.current_node.report:
            raise ValueError(
                "Cannot focus up without writing a report first. Please use the write_report command to document your findings."
            )
        
        if not self.file_system.current_node.parent:
            self.finished = True

        self.file_system.focus_up()
        # Clear history when changing focus
        self.chat_history.clear()
        
        # Print updated status after focus change
        self._print_current_status()
        
    def _handle_fail_problem_and_focus_up(self, args: dict):
        """Handle fail_problem_and_focus_up command - similar to focus_up but without report requirement"""
        if not self.file_system.current_node:
            return
            
        # For now, we'll treat this the same as focus_up but without the report requirement
        if not self.file_system.current_node.parent:
            self.finished = True
            
        self.file_system.focus_up()
        # Clear history when changing focus
        self.chat_history.clear()
        
        # Print updated status after focus change
        self._print_current_status()

    def _handle_add_criteria_to_subproblem(self, args: dict):
        """Handle add_criteria_to_subproblem command"""
        if not self.file_system.current_node:
            return

        # Get the subproblem by title
        title = args["title"]
        if title not in self.file_system.current_node.subproblems:
            return

        subproblem = self.file_system.current_node.subproblems[title]

        # Add criteria to the subproblem
        criteria_text = args["criteria"]
        if criteria_text in subproblem.criteria:
            return

        subproblem.add_criteria(criteria_text)
        self.file_system.update_files()

    def _print_current_status(self):
        """Print the current status of the research to STDOUT"""
        if not self.problem_defined:
            print("\n=== Deep Research Assistant ===")
            print("Status: No problem defined yet")
            return
            
        if not self.file_system.current_node:
            print("\n=== Deep Research Assistant ===")
            print("Status: No current node")
            return
            
        print("\n" + "="*80)
        print("=== Deep Research Assistant - Comprehensive Progress Report ===")
        
        # Print current problem info
        current_node = self.file_system.current_node
        print(f"Current Problem: {current_node.title}")
        
        # Print criteria status
        criteria_met = current_node.get_criteria_met_count()
        criteria_total = current_node.get_criteria_total_count()
        print(f"Criteria Status: {criteria_met}/{criteria_total} met")
        
        # Print report status
        report_status = "✓ Written" if current_node.report else "✗ Not written"
        print(f"Report Status: {report_status}")
        
        # Print full problem tree with detailed metadata
        print("\n=== Full Problem Tree ===")
        self._print_problem_tree(self.file_system.root_node, "", True, current_node)
        
        print("="*80 + "\n")
    
    def _print_problem_tree(self, node, prefix, is_last, current_node):
        """Print a tree representation of the problem hierarchy with metadata"""
        if not node:
            return
            
        # Determine the branch symbol
        branch = "└── " if is_last else "├── "
        
        # Highlight current node
        is_current = node == current_node
        node_marker = "→ " if is_current else ""
        
        # Gather metadata
        criteria_met = node.get_criteria_met_count()
        criteria_total = node.get_criteria_total_count()
        report_indicator = "📄" if node.report else "  "
        attachments_count = len(node.attachments)
        subproblems_count = len(node.subproblems)
        
        # Format the node line with metadata
        node_info = f"{node_marker}{node.title} [{criteria_met}/{criteria_total}] {report_indicator}"
        if attachments_count > 0:
            node_info += f" 📎{attachments_count}"
        if subproblems_count > 0:
            node_info += f" 🔍{subproblems_count}"
            
        # Print the current node
        print(f"{prefix}{branch}{node_info}")
        
        # Prepare prefix for children
        new_prefix = prefix + ("    " if is_last else "│   ")
        
        # Print all subproblems
        subproblems = list(node.subproblems.values())
        for i, subproblem in enumerate(subproblems):
            is_last_child = i == len(subproblems) - 1
            self._print_problem_tree(subproblem, new_prefix, is_last_child, current_node)


