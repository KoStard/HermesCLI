import os
import sys
from typing import List, Optional

from .command_parser import CommandParser
from .file_system import FileSystem
from .interface import Interface


class DeepResearchApp:
    def __init__(self, instruction: str, initial_attachments: List[str] = None, root_dir: str = "research"):
        self.file_system = FileSystem(root_dir)
        self.interface = Interface(self.file_system, instruction)
        self.command_parser = CommandParser()
        self.initial_attachments = initial_attachments or []
        self.problem_defined = False
        self.finished = False

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
        os.system('cls' if os.name == 'nt' else 'clear')
        
        if not self.problem_defined:
            print(self.interface.render_no_problem_defined(self.initial_attachments))
        else:
            print(self.interface.render_problem_defined())

    def _get_multiline_input(self) -> str:
        """Get multiline input from the user"""
        print("\n--- Enter your response (press Esc+Enter to finish) ---")
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
        command, args = self.command_parser.parse(text)
        
        if command:
            self._execute_command(command, args)
        else:
            print("\nNo command detected. Please use one of the available commands.")
            input("Press Enter to continue...")
        
        self._render_interface()

    def _execute_command(self, command: str, args: dict):
        """Execute a command"""
        if "error" in args:
            print(f"\nError in command: {args['error']}")
            input("Press Enter to continue...")
            return
        
        if not self.problem_defined:
            if command == "define_problem":
                self._handle_define_problem(args)
            else:
                print("\nYou need to define a problem first.")
                input("Press Enter to continue...")
            return
        
        # Commands available when problem is defined
        command_handlers = {
            "add_criteria": self._handle_add_criteria,
            "mark_criteria_as_done": self._handle_mark_criteria_as_done,
            "add_subproblem": self._handle_add_subproblem,
            "add_attachment": self._handle_add_attachment,
            "write_report": self._handle_write_report,
            "append_to_problem_definition": self._handle_append_to_problem_definition,
            "focus_down": self._handle_focus_down,
            "focus_up": self._handle_focus_up,
            "finish_task": self._handle_finish_task,
        }
        
        if command in command_handlers:
            command_handlers[command](args)
        else:
            print(f"\nUnknown command: {command}")
            input("Press Enter to continue...")

    def _handle_define_problem(self, args: dict):
        """Handle define_problem command"""
        self.file_system.create_root_problem(args["title"], args["content"])
        
        # Copy initial attachments to the root problem
        for attachment in self.initial_attachments:
            self.file_system.current_node.add_attachment(
                attachment, 
                f"Content of {attachment} would be here..."
            )
        
        # Ensure file system is fully updated
        self.file_system.update_files()
        
        self.problem_defined = True
        print("\nProblem defined successfully!")
        print(f"Files created in directory: {self.file_system.root_dir}")
        input("Press Enter to continue...")

    def _handle_add_criteria(self, args: dict):
        """Handle add_criteria command"""
        if not self.file_system.current_node:
            return
        
        index = self.file_system.current_node.add_criteria(args["criteria"])
        self.file_system.update_files()
        print(f"\nCriteria added with index {index + 1}")
        input("Press Enter to continue...")

    def _handle_mark_criteria_as_done(self, args: dict):
        """Handle mark_criteria_as_done command"""
        if not self.file_system.current_node:
            return
        
        success = self.file_system.current_node.mark_criteria_as_done(args["index"])
        if success:
            self.file_system.update_files()
            print(f"\nCriteria {args['index'] + 1} marked as done")
        else:
            print(f"\nInvalid criteria index: {args['index'] + 1}")
        input("Press Enter to continue...")

    def _handle_add_subproblem(self, args: dict):
        """Handle add_subproblem command"""
        if not self.file_system.current_node:
            return
        
        subproblem = self.file_system.current_node.add_subproblem(args["title"], args["content"])
        # Create directories for the new subproblem
        self.file_system._create_node_directories(subproblem)
        self.file_system.update_files()
        print(f"\nSubproblem '{args['title']}' added")
        if subproblem.path:
            print(f"Files created in directory: {subproblem.path}")
        input("Press Enter to continue...")

    def _handle_add_attachment(self, args: dict):
        """Handle add_attachment command"""
        if not self.file_system.current_node:
            return
        
        self.file_system.current_node.add_attachment(args["name"], args["content"])
        self.file_system.update_files()
        print(f"\nAttachment '{args['name']}' added")
        input("Press Enter to continue...")

    def _handle_write_report(self, args: dict):
        """Handle write_report command"""
        if not self.file_system.current_node:
            return
        
        self.file_system.current_node.write_report(args["content"])
        self.file_system.update_files()
        print("\nReport written successfully")
        input("Press Enter to continue...")

    def _handle_append_to_problem_definition(self, args: dict):
        """Handle append_to_problem_definition command"""
        if not self.file_system.current_node:
            return
        
        self.file_system.current_node.append_to_problem_definition(args["content"])
        self.file_system.update_files()
        print("\nProblem definition updated")
        input("Press Enter to continue...")

    def _handle_focus_down(self, args: dict):
        """Handle focus_down command"""
        if not self.file_system.current_node:
            return
        
        result = self.file_system.focus_down(args["title"])
        if result:
            print(f"\nFocused down to '{args['title']}'")
        else:
            print(f"\nSubproblem '{args['title']}' not found")
        input("Press Enter to continue...")

    def _handle_focus_up(self, args: dict):
        """Handle focus_up command"""
        if not self.file_system.current_node or not self.file_system.current_node.parent:
            print("\nAlready at the root problem")
            input("Press Enter to continue...")
            return
        
        self.file_system.focus_up()
        print("\nFocused up to parent problem")
        input("Press Enter to continue...")

    def _handle_finish_task(self, args: dict):
        """Handle finish_task command"""
        if not self.file_system.current_node or self.file_system.current_node != self.file_system.root_node:
            print("\nYou can only finish the task from the root problem")
            input("Press Enter to continue...")
            return
        
        # Check if all criteria are met and report is written
        node = self.file_system.current_node
        all_criteria_met = all(node.criteria_done) if node.criteria else False
        has_report = bool(node.report)
        
        if not all_criteria_met:
            print("\nCannot finish task: Not all criteria are met")
            input("Press Enter to continue...")
            return
        
        if not has_report:
            print("\nCannot finish task: No report has been written")
            input("Press Enter to continue...")
            return
        
        print("\nTask finished successfully!")
        print("Thank you for using Deep Research Interface.")
        print(f"All research files are saved in: {self.file_system.root_dir}")
        input("Press Enter to exit...")
        self.finished = True
