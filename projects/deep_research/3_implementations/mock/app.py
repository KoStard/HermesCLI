import os
import sys
from typing import List, Optional

from .command_parser import CommandParser, ParseResult
from .file_system import FileSystem
from .history import ChatHistory
from .interface import Interface


class DeepResearchApp:
    def __init__(
        self,
        instruction: str,
        initial_attachments: List[str] = None,
        root_dir: str = "research",
    ):
        self.file_system = FileSystem(root_dir)
        self.chat_history = ChatHistory()
        self.interface = Interface(self.file_system, instruction)
        self.command_parser = CommandParser()
        self.initial_attachments = initial_attachments or []
        self.finished = False

        # Check if problem already exists
        existing_problem = self.file_system.load_existing_problem()
        self.problem_defined = existing_problem is not None

    def start(self):
        """Start the application"""
        self._render_interface()

        while not self.finished:
            try:
                user_input = self._get_multiline_input()
                self._process_input(user_input)
            except KeyboardInterrupt:
                print("\nExiting application...")
                break
            except Exception as e:
                print(f"Error: {e}")

    def _render_interface(self):
        """Render the interface"""
        os.system("cls" if os.name == "nt" else "clear")

        # First render the interface
        if not self.problem_defined:
            interface_content = self.interface.render_no_problem_defined(
                self.initial_attachments
            )
            print(interface_content)
        else:
            interface_content = self.interface.render_problem_defined()
            print(interface_content)

        # Always render the chat history regardless of problem definition status
        if self.chat_history.messages:
            print("\n" + "=" * 70)
            print("# CHAT HISTORY")
            print("=" * 70)
            print(self.chat_history.get_formatted_history())

    def _get_multiline_input(self) -> str:
        """Get multiline input from the user"""
        lines = []

        while True:
            try:
                line = input()
                if line == "\x1b":  # Escape character
                    break
                lines.append(line)
            except EOFError:
                break

        return "\n".join(lines)

    def _process_input(self, text: str):
        """Process user input"""
        # Add the assistant's message to history
        # Always add to history regardless of problem definition status
        self.chat_history.add_message("Assistant", text)

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
            self.chat_history.add_message("User", auto_reply)
        else:
            # Execute commands if there are no syntax errors
            commands_executed = False

            for result in parse_results:
                if result.command and not result.errors:
                    try:
                        self._execute_command(result.command, result.args)
                        execution_status[result.command] = "success"
                        commands_executed = True
                    except Exception as e:
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
                self.chat_history.add_message("User", auto_reply)

        # Re-render the interface after processing commands
        self._render_interface()

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
            "finish_task": self._handle_finish_task,
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

    def _handle_focus_up(self, args: dict):
        """Handle focus_up command"""
        if (
            not self.file_system.current_node
            or not self.file_system.current_node.parent
        ):
            return

        # Check if report is written before allowing focus_up
        if not self.file_system.current_node.report:
            raise Exception(
                "Cannot focus up without writing a report first. Please use the write_report command to document your findings."
            )

        self.file_system.focus_up()
        # Clear history when changing focus
        self.chat_history.clear()

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

    def _handle_finish_task(self, args: dict):
        """Handle finish_task command"""
        if (
            not self.file_system.current_node
            or self.file_system.current_node != self.file_system.root_node
        ):
            return

        # Check if all criteria are met and report is written
        node = self.file_system.current_node
        all_criteria_met = all(node.criteria_done) if node.criteria else False
        has_report = bool(node.report)

        if not all_criteria_met or not has_report:
            return

        self.finished = True
