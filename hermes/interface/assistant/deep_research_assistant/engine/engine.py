import os
import time
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from .command_parser import CommandParser, ParseResult
from .file_system import FileSystem, ProblemStatus
from .history import ChatHistory
from .interface import DeepResearcherInterface
from .llm_interface import LLMInterface
from .logger import DeepResearchLogger
from .task_executor import TaskExecutor
from .task_queue import TaskStatus


class DeepResearchEngine:
    """Core engine for Deep Research functionality, independent of UI implementation"""
    
    def __init__(
        self,
        instruction: str,
        initial_attachments: List[str] = None,
        root_dir: str = "research",
        llm_interface: LLMInterface = None,
    ):
        self.file_system = FileSystem(root_dir)
        self.chat_history = ChatHistory()
        self.command_parser = CommandParser()
        self.initial_attachments = initial_attachments or []
        self.finished = False
        self.logger = DeepResearchLogger(Path(root_dir))
        self.llm_interface = llm_interface

        # Check if problem already exists
        existing_problem = self.file_system.load_existing_problem()
        self.problem_defined = existing_problem is not None
        
        # Initialize task executor
        self.task_executor = TaskExecutor(self.file_system)
        
        # Initialize interface with the file system
        self.interface = DeepResearcherInterface(self.file_system, instruction)
        
        self.current_node = None
        # TODO: Could move to the file system
        self.permanent_log = []
        
        # Print initial status
        self._print_current_status()
    
    def get_interface_content(self) -> str:
        """Get the current interface content as a string"""
        if not self.problem_defined:
            return self.interface.render_no_problem_defined(self.initial_attachments)
        else:
            return self.interface.render_problem_defined(self.current_node, self.permanent_log)
    
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
            auto_reply = f'Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done using `focus_up` command.\n\n{error_report}'
            self.chat_history.add_message("user", auto_reply)
            print(auto_reply)
            self._print_current_status()
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
            auto_reply = f'Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done using `focus_up` command.'
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
            "add_artifact": self._handle_add_artifact,
            "append_to_problem_definition": self._handle_append_to_problem_definition,
            "add_criteria_to_subproblem": self._handle_add_criteria_to_subproblem,
            "focus_down": self._handle_focus_down,
            "focus_up": self._handle_focus_up,
            "fail_problem_and_focus_up": self._handle_fail_problem_and_focus_up,
            "cancel_subproblem": self._handle_cancel_subproblem,
            "add_log_entry": self._handle_add_log_entry,
        }

        if command in command_handlers:
            command_handlers[command](args)
        else:
            # This error will be captured in the error report
            pass

    def _handle_define_problem(self, args: dict):
        """Handle define_problem command"""
        root_node = self.file_system.create_root_problem(args["title"], args["content"])
        
        # Set the root node status to CURRENT
        root_node.status = ProblemStatus.CURRENT

        # Copy initial artifacts to the root problem
        for artifact in self.initial_attachments:
            root_node.add_artifact(
                artifact, f"Content of {artifact} would be here..."
            )

        # Ensure file system is fully updated
        self.file_system.update_files()

        # Clear history as we're starting fresh with a defined problem
        self.chat_history.clear()

        self.problem_defined = True
        
        # Initialize the task executor with the root node
        self.task_executor._initialize_root_task()
        self.current_node = self.task_executor.get_current_node()
        
    def _handle_add_criteria(self, args: dict):
        """Handle add_criteria command"""
        current_node = self.current_node
        if not current_node:
            return

        # Check if criteria already exists (per requirements in 3 - commands.md)
        criteria_text = args["criteria"]
        if criteria_text in current_node.criteria:
            return

        index = current_node.add_criteria(criteria_text)
        self.file_system.update_files()

    def _handle_mark_criteria_as_done(self, args: dict):
        """Handle mark_criteria_as_done command"""
        current_node = self.current_node
        if not current_node:
            return

        success = current_node.mark_criteria_as_done(args["index"])
        if success:
            self.file_system.update_files()

    def _handle_add_subproblem(self, args: dict):
        """Handle add_subproblem command"""
        current_node = self.current_node
        if not current_node:
            return

        # Check if subproblem with this title already exists
        title = args["title"]
        if title in current_node.subproblems:
            return

        subproblem = current_node.add_subproblem(
            title, args["content"]
        )
        # Set initial status to NOT_STARTED
        subproblem.status = ProblemStatus.NOT_STARTED
        # Create directories for the new subproblem
        self.file_system._create_node_directories(subproblem)
        self.file_system.update_files()

    def _handle_add_artifact(self, args: dict):
        """Handle add_artifact command"""
        current_node = self.current_node
        if not current_node:
            return

        current_node.add_artifact(args["name"], args["content"])
        self.file_system.update_files()

    def _handle_append_to_problem_definition(self, args: dict):
        """Handle append_to_problem_definition command"""
        current_node = self.current_node
        if not current_node:
            return

        current_node.append_to_problem_definition(args["content"])
        self.file_system.update_files()

    def _handle_focus_down(self, args: dict):
        """Handle focus_down command"""
        # Request focus down through the task executor
        title = args["title"]
        result = self.task_executor.request_focus_down(title)
        
        if result:
            # Get the previous node before updating current_node
            previous_node = self.current_node
            
            # Update current_node to the new focus
            self.current_node = self.task_executor.get_current_node()
            
            # Update statuses
            if previous_node:
                # Set parent to PENDING (focus moved to child)
                previous_node.status = ProblemStatus.PENDING
                
            # Set current node to CURRENT
            self.current_node.status = ProblemStatus.CURRENT
            
            # Update the file system
            self.file_system.update_files()
            
            # Clear history when changing focus
            self.chat_history.clear()
        else:
            raise ValueError(
                f"Failed to focus down to subproblem '{title}'. Make sure the subproblem exists."
            )

    def _handle_focus_up(self, args: dict):
        """Handle focus_up command"""
        # Store the current node before focusing up
        previous_node = self.current_node
        
        # Mark the current node as FINISHED before focusing up
        if previous_node:
            previous_node.status = ProblemStatus.FINISHED
            self.file_system.update_files()
            
        # Request focus up through the task executor
        result = self.task_executor.request_focus_up()
        
        if result:
            # Update current_node to the new focus (parent)
            self.current_node = self.task_executor.get_current_node()
            
            # Set the new current node to CURRENT
            if self.current_node:
                self.current_node.status = ProblemStatus.CURRENT
                self.file_system.update_files()
                
            # Clear history when changing focus
            self.chat_history.clear()
            
            # Check if we've finished the root task
            if not self.current_node:
                self.finished = True
        else:
            return
        
    def _handle_add_log_entry(self, args: dict):
        """Handle add_log_entry command"""
        content = args.get("content", "")
        if content:
            self.permanent_log.append(content)

    def _handle_fail_problem_and_focus_up(self, args: dict):
        """Handle fail_problem_and_focus_up command - similar to focus_up but without report requirement"""
        # Store the current node before focusing up
        previous_node = self.current_node
        
        # Mark the current node as FAILED before focusing up
        if previous_node:
            previous_node.status = ProblemStatus.FAILED
            self.file_system.update_files()
            
        # Request fail and focus up through the task executor
        result = self.task_executor.request_fail_and_focus_up()
        
        if result:
            # Update current_node to the new focus (parent)
            self.current_node = self.task_executor.get_current_node()
            
            # Set the new current node to CURRENT
            if self.current_node:
                self.current_node.status = ProblemStatus.CURRENT
                self.file_system.update_files()
                
            # Clear history when changing focus
            self.chat_history.clear()
            
            # Check if we've finished the root task
            if not self.current_node:
                self.finished = True
        else:
            raise ValueError(
                "Failed to mark problem as failed and focus up. This should not happen."
            )
            
    def _handle_cancel_subproblem(self, args: dict):
        """Handle cancel_subproblem command"""
        current_node = self.current_node
        if not current_node:
            return
            
        # Get the subproblem by title
        title = args["title"]
        if title not in current_node.subproblems:
            raise ValueError(f"Subproblem '{title}' not found")
            
        subproblem = current_node.subproblems[title]
        
        # Mark the subproblem as cancelled
        subproblem.status = ProblemStatus.CANCELLED
        
        # Update the file system
        self.file_system.update_files()

    def _handle_add_criteria_to_subproblem(self, args: dict):
        """Handle add_criteria_to_subproblem command"""
        current_node = self.current_node
        if not current_node:
            return

        # Get the subproblem by title
        title = args["title"]
        if title not in current_node.subproblems:
            return

        subproblem = current_node.subproblems[title]

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
            
        current_node = self.current_node
        if not current_node:
            print("\n=== Deep Research Assistant ===")
            print("Status: No current node")
            return
            
        print("\n" + "="*80)
        print("=== Deep Research Assistant - Comprehensive Progress Report ===")
        
        # Print current problem info
        print(f"Current Problem: {current_node.title}")
        
        # Print criteria status
        criteria_met = current_node.get_criteria_met_count()
        criteria_total = current_node.get_criteria_total_count()
        print(f"Criteria Status: {criteria_met}/{criteria_total} met")
        
        
        # Print task status information
        if self.task_executor.current_task_id:
            current_task = self.task_executor.task_queue.get_task(self.task_executor.current_task_id)
            if current_task:
                print(f"Task Status: {current_task.status.value}")
                
                # Print pending child tasks if any
                if self.task_executor.current_task_id in self.task_executor.task_relationships:
                    child_task_ids = self.task_executor.task_relationships[self.task_executor.current_task_id]
                    pending_children = 0
                    running_children = 0
                    completed_children = 0
                    failed_children = 0
                    
                    for child_id in child_task_ids:
                        child_task = self.task_executor.task_queue.get_task(child_id)
                        if child_task:
                            if child_task.status == TaskStatus.PENDING:
                                pending_children += 1
                            elif child_task.status == TaskStatus.RUNNING:
                                running_children += 1
                            elif child_task.status == TaskStatus.COMPLETED:
                                completed_children += 1
                            elif child_task.status == TaskStatus.FAILED:
                                failed_children += 1
                    
                    if pending_children + running_children + completed_children + failed_children > 0:
                        print(f"Child Tasks: {pending_children} pending, {running_children} running, "
                              f"{completed_children} completed, {failed_children} failed")
        
        # Print full problem tree with detailed metadata
        print("\n=== Full Problem Tree ===")
        self._print_problem_tree(self.file_system.root_node, "", True, current_node)
        
        print("="*80 + "\n")
    
    def execute(self) -> str:
        """
        Execute the deep research process and return the final report
        
        Returns:
            str: Final report
        """
        while not self.finished:
            self.current_node = self.task_executor.get_current_node()
            
            # Get the interface content
            interface_content = self.get_interface_content()
            
            # Convert history messages to dict format for the LLM interface
            history_messages = [
                {"author": message.author, "content": message.content}
                for message in self.chat_history.messages
            ]
            
            # Generate the request
            request = self.llm_interface.generate_request(interface_content, history_messages)
            
            # Get the current node path for logging
            current_node_path = self.current_node.path if self.current_node else self.file_system.root_dir
                
            # Log the request
            self.llm_interface.log_request(
                current_node_path,
                [{"author": "user", "text": interface_content}] + history_messages,
                request
            )
            
            # Process the request and get the response
            response_generator = self.llm_interface.send_request(request)
            
            # Get the full response
            full_llm_response = next(response_generator)
            
            # Log the response
            self.llm_interface.log_response(current_node_path, full_llm_response)
            
            # Process the commands in the response
            self.process_commands(full_llm_response)
            
            # If there's no current task, we need to check if we're done or if we need to start another task
            if not self.task_executor.current_task_id:
                # Check if there are any pending tasks
                pending_tasks = self.task_executor.task_queue.get_tasks_by_status(TaskStatus.PENDING)
                if not pending_tasks:
                    # No more tasks, we're done
                    self.finished = True
        
        # Generate the final report
        return self._generate_final_report()
    
    def _generate_final_report(self) -> str:
        """Generate a summary of all artifacts created during the research"""
        if not self.file_system.root_node:
            return "Research completed, but no artifacts were generated."
        
        # Collect all artifacts from the entire problem hierarchy
        all_artifacts = self.interface.collect_artifacts_recursively(self.file_system.root_node)
        
        if not all_artifacts:
            return "Research completed, but no artifacts were generated."
        
        # Group artifacts by problem
        artifacts_by_problem = {}
        for owner_title, name, _ in all_artifacts:
            if owner_title not in artifacts_by_problem:
                artifacts_by_problem[owner_title] = []
            artifacts_by_problem[owner_title].append(name)
        
        # Generate the report
        result = f"""# Deep Research Completed

## Problem: {self.file_system.root_node.title}

## Summary of Generated Artifacts

The research has been completed and the following artifacts have been created:

"""
        
        # List all artifacts with their filepaths
        for problem_title, artifact_names in artifacts_by_problem.items():
            result += f"### {problem_title}\n\n"
            for name in artifact_names:
                # Construct the relative filepath
                filepath = f"Artifacts/{name}"
                result += f"- `{filepath}`: {name}\n"
            result += "\n"
        
        result += """
These artifacts contain the valuable outputs of the research process. Each artifact represents
a concrete piece of knowledge or analysis that contributes to solving the root problem.
"""
        
        return result
    
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
        artifacts_count = len(node.artifacts)
        subproblems_count = len(node.subproblems)
        
        # Get status emoji
        status_emoji = node.get_status_emoji()
        
        # Format the node line with metadata
        node_info = f"{node_marker}{status_emoji} {node.title} [{criteria_met}/{criteria_total}]"
        if artifacts_count > 0:
            node_info += f" 🗂️{artifacts_count}"
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


