import os
import time
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from .command import CommandRegistry
from .command_parser import CommandParser, ParseResult
# Import commands to ensure they're registered
from . import commands
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
        extension_commands: List = None,
    ):
        self.file_system = FileSystem(root_dir)
        self.chat_history = ChatHistory()
        self.command_parser = CommandParser()
        self.initial_attachments = initial_attachments or []
        self.finished = False
        self.logger = DeepResearchLogger(Path(root_dir))
        self.llm_interface = llm_interface
        self.current_node = None

        # Check if problem already exists
        existing_problem = self.file_system.load_existing_problem()
        self.problem_defined = existing_problem is not None
        
        # Set current node to root node if problem is already defined
        if self.problem_defined:
            self.current_node = existing_problem
        
        # Initialize task executor
        self.task_executor = TaskExecutor(self.file_system)
        
        # Register any extension commands
        if extension_commands:
            for command_class in extension_commands:
                CommandRegistry().register(command_class())
        
        self._extension_commands = extension_commands
        
        # Initialize interface with the file system
        self.interface = DeepResearcherInterface(self.file_system, instruction)
        
        # TODO: Could move to the file system
        self.permanent_log = []
        
        # Store command outputs for automatic responses
        self.command_outputs = {}
        
        # Print initial status
        self._print_current_status()
    
    def get_interface_content(self) -> str:
        """Get the current interface content as a string"""
        if not self.problem_defined:
            return self.interface.render_no_problem_defined(self.initial_attachments)
        else:
            return self.interface.render_problem_defined(self.current_node, self.permanent_log)
    
    def add_command_output(self, command_name: str, args: Dict, output: str) -> None:
        """
        Add command output to be included in the automatic response
        
        Args:
            command_name: Name of the command
            args: Arguments passed to the command
            output: Output text to display
        """
        if command_name not in self.command_outputs:
            self.command_outputs[command_name] = []
            
        self.command_outputs[command_name].append({
            "args": args,
            "output": output
        })
    
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
            if result.command_name and not result.errors:
                try:
                    self._execute_command(result.command_name, result.args)
                    execution_status[result.command_name] = "success"
                    commands_executed = True
                except ValueError as e:
                    execution_status[result.command_name] = f"failed: {str(e)}"

        # Add execution status to error report if there were failures
        if any(status.startswith("failed") for status in execution_status.values()):
            if not error_report:
                error_report = "### Execution Status Report:\n"
            else:
                error_report += "\n### Execution Status Report:\n"

            for cmd, status in execution_status.items():
                if status.startswith("failed"):
                    error_report += f"- Command '{cmd}' {status}\n"

        auto_reply = f'Automatic Reply: The status of the research is "In Progress". Please continue the research or mark it as done using `focus_up` command.'
        if error_report:
            auto_reply += f"\n\n{error_report}"
            
        # Add command outputs if any
        if self.command_outputs:
            auto_reply += "\n\n### Command Outputs\n"
            for cmd_name, outputs in self.command_outputs.items():
                for output_data in outputs:
                    auto_reply += f"\n#### {cmd_name}\n"
                    # Format arguments
                    args_str = ", ".join(f"{k}: {v}" for k, v in output_data["args"].items())
                    if args_str:
                        auto_reply += f"Arguments: {args_str}\n\n"
                    # Add the output
                    auto_reply += f"```\n{output_data['output']}\n```\n"
            
            # Clear command outputs after adding them to the response
            self.command_outputs = {}
            
        self.chat_history.add_message("user", auto_reply)
        print(auto_reply)
        
        self._print_current_status()
        return commands_executed, error_report, execution_status

    def _execute_command(self, command_name: str, args: dict):
        """Execute a command"""
        registry = CommandRegistry()
        command = registry.get_command(command_name)
        
        if not command:
            # This error will be captured in the error report
            return
            
        if not self.problem_defined and command_name != "define_problem":
            # Only define_problem is allowed when problem is not defined
            return
            
        # Execute the command
        command.execute(self, args)


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
        # Check if LLM interface is available
        if not self.llm_interface:
            raise ValueError("LLM interface is required for execution")
            
        # Initialize current node if problem is already defined
        if self.problem_defined and not self.current_node:
            self.current_node = self.file_system.root_node
            
        while not self.finished:
            # Only update current node from task executor if it's not already set
            if not self.current_node:
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
            try:
                full_llm_response = next(response_generator)
            except StopIteration:
                full_llm_response = ""
            
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


