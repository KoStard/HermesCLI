from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from .command import CommandRegistry
from .command_parser import CommandParser, ParseResult
from .command_context import CommandContext

# Import commands to ensure they're registered
from .file_system import FileSystem, Node, ProblemStatus
from .history import ChatHistory, AutoReply, ChatMessage
from .interface import DeepResearcherInterface
from .llm_interface import LLMInterface
from .logger import DeepResearchLogger
from .status_printer import StatusPrinter
from .report_generator import ReportGenerator


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

        # TODO: Could move to the file system
        self.permanent_log = []

        # Create command context for commands to use - shared across all commands
        self.command_context = CommandContext(self)

        # Set current node to root node if problem is already defined
        if self.problem_defined:
            self.activate_node(existing_problem)

        # Register any extension commands
        if extension_commands:
            for command_class in extension_commands:
                CommandRegistry().register(command_class())

        self._extension_commands = extension_commands

        # Initialize interface with the file system
        self.interface = DeepResearcherInterface(self.file_system, instruction)
        
        # Store command outputs for automatic responses
        self.command_outputs = {}

        # Print initial status
        self._print_current_status()

    def get_interface_content(self) -> str:
        """Get the current interface content as a string"""
        if not self.problem_defined:
            return self.interface.render_no_problem_defined(self.initial_attachments)
        else:
            return self.interface.render_problem_defined(
                self.current_node, self.permanent_log
            )

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

        self.command_outputs[command_name].append({"args": args, "output": output})

    def process_commands(self, text: str) -> tuple[bool, str, Dict]:
        """
        Process commands from text

        Returns:
            tuple: (commands_executed, error_report, execution_status)
        """
        # Check for emergency shutdown code
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            self.finished = True
            return (
                True,
                "System shutdown requested and executed.",
                {"shutdown": "success"},
            )

        # Add the assistant's message to history for the current node
        self.chat_history.add_message("assistant", text)

        # Parse all commands from the text
        parse_results = self.command_parser.parse_text(text)

        # Check for errors
        has_errors = any(result.errors for result in parse_results)

        # Track execution status for reporting
        # Use a dictionary with command names as keys and a list of status entries as values
        # to handle multiple commands with the same name
        execution_status = {}

        # Generate error report if there are errors
        error_report = ""
        if has_errors:
            error_report = self.command_parser.generate_error_report(parse_results)

        # Execute commands that don't have syntax errors
        commands_executed = False

        for i, result in enumerate(parse_results):
            if result.command_name and not result.has_syntax_error:
                # Create a unique key for this command instance
                cmd_key = f"{result.command_name}_{i}"
                line_num = result.errors[0].line_number if result.errors else None

                if not result.errors:
                    try:
                        self._execute_command(result.command_name, result.args)
                        execution_status[cmd_key] = {
                            "name": result.command_name,
                            "status": "success",
                            "line": line_num,
                        }
                        commands_executed = True
                    except ValueError as e:
                        execution_status[cmd_key] = {
                            "name": result.command_name,
                            "status": f"failed: {str(e)}",
                            "line": line_num,
                        }
                else:
                    # Command has validation errors but not syntax errors
                    execution_status[cmd_key] = {
                        "name": result.command_name,
                        "status": "failed: validation errors",
                        "line": line_num,
                    }

        # Add execution status to error report if there were failures
        failed_commands = [
            info
            for info in execution_status.values()
            if info["status"].startswith("failed")
        ]

        if failed_commands:
            if not error_report:
                error_report = "### Execution Status Report:\n"
            else:
                error_report += "\n### Execution Status Report:\n"

            for info in failed_commands:
                cmd_name = info["name"]
                status = info["status"]
                line_num = info["line"]
                line_info = f" at line {line_num}" if line_num else ""
                error_report += f"- Command '{cmd_name}'{line_info} {status}\n"

        auto_reply = AutoReply(error_report, self.command_outputs)
        
        # Clear command outputs after adding them to the response
        self.command_outputs = {}

        # Add the auto reply to the current node's history
        self.chat_history.add_auto_reply(auto_reply)

        self._print_current_status(auto_reply.generate_auto_reply())
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

        # Update command context with latest state before each command execution
        self.command_context.refresh_from_engine()
        
        # Execute the command with the context instead of the engine
        command.execute(self.command_context, args)

    def _print_current_status(self, auto_reply: str = None):
        """Print the current status of the research to STDOUT"""
        if auto_reply:
            print(auto_reply)
        status_printer = StatusPrinter()
        status_printer.print_status(
            self.problem_defined,
            self.current_node,
            self.file_system
        )

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
            self.activate_node(self.file_system.root_node)

        while not self.finished:
            # Get the interface content
            interface_content = self.get_interface_content()

            # Convert history messages to dict format for the LLM interface
            history_messages = []

            auto_reply_counter = 0
            auto_reply_max_length = None
            for block in self.chat_history.blocks[::-1]:  # Reverse to handle auto reply contraction
                if isinstance(block, ChatMessage):
                    history_messages.append(
                        {"author": block.author, "content": block.content}
                    )
                elif isinstance(block, AutoReply):
                    auto_reply_counter += 1
                    if auto_reply_counter > 1:
                        if not auto_reply_max_length:
                            auto_reply_max_length = 5_000
                        else:
                            auto_reply_max_length = max(auto_reply_max_length / 2, 300)
                    history_messages.append(
                        {
                            "author": "user",
                            "content": block.generate_auto_reply(auto_reply_max_length),
                        }
                    )

            history_messages = history_messages[::-1]  # Reverse to maintain chronological order

            # Generate the request
            request = self.llm_interface.generate_request(
                interface_content, history_messages
            )

            # Get the current node path for logging
            current_node_path = (
                self.current_node.path
                if self.current_node
                else self.file_system.root_dir
            )

            # Log the request
            self.llm_interface.log_request(
                current_node_path,
                [{"author": "user", "text": interface_content}] + history_messages,
                request,
            )

            # Process the request and get the response
            while True:
                try:
                    response_generator = self.llm_interface.send_request(request)

                    # Get the full response
                    try:
                        full_llm_response = next(response_generator)
                        break  # Successfully got a response, exit the retry loop
                    except StopIteration:
                        full_llm_response = ""
                        break  # Empty response but not an error, exit the retry loop
                except Exception as e:
                    import traceback

                    print("\n\n===== LLM INTERFACE ERROR =====")
                    print(traceback.format_exc())
                    print("===============================")
                    print("\nPress Enter to retry or Ctrl+C to exit...")
                    try:
                        input()  # Wait for user input
                        print("Retrying LLM request...")
                    except KeyboardInterrupt:
                        print("\nExiting due to user request.")
                        return "Research terminated due to LLM interface error."

            # Log the response
            self.llm_interface.log_response(current_node_path, full_llm_response)

            # Process the commands in the response
            self.process_commands(full_llm_response)

        # Generate the final report
        return self._generate_final_report()

    def activate_node(self, node: Node) -> None:
        """Set the current node and update chat history"""
        self.current_node = node
        self.chat_history.set_current_node(node.title)

    def _generate_final_report(self) -> str:
        """Generate a summary of all artifacts created during the research"""
        report_generator = ReportGenerator(self.file_system)
        return report_generator.generate_final_report(self.interface)
        
    def focus_down(self, subproblem_title: str) -> bool:
        """
        Focus down to a subproblem
        
        Args:
            subproblem_title: Title of the subproblem to focus on
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_node:
            return False
            
        # Check if the subproblem exists
        if subproblem_title not in self.current_node.subproblems:
            return False
            
        # Get the subproblem
        subproblem = self.current_node.subproblems[subproblem_title]
        
        # Set the parent to PENDING
        self.current_node.status = ProblemStatus.PENDING
        
        # Set the subproblem to CURRENT
        subproblem.status = ProblemStatus.CURRENT
        
        # Update the current node
        self.activate_node(subproblem)
        
        # Update files
        self.file_system.update_files()
        
        return True
        
    def focus_up(self) -> bool:
        """
        Focus up to the parent problem
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_node:
            return False
            
        # Get the parent chain
        parent_chain = self.file_system.get_parent_chain(self.current_node)
        
        # If this is the root node, we're done
        if len(parent_chain) <= 1:
            # Mark the root node as FINISHED
            self.current_node.status = ProblemStatus.FINISHED
            self.file_system.update_files()
            self.finished = True
            return True
            
        # Mark the current node as FINISHED
        self.current_node.status = ProblemStatus.FINISHED
        
        # Get the parent node (second to last in the chain, as the last is the current node)
        parent_node = parent_chain[-2]
        
        # Set the parent to CURRENT
        parent_node.status = ProblemStatus.CURRENT
        
        # Update the current node
        self.activate_node(parent_node)
        
        # Update files
        self.file_system.update_files()
        
        return True
        
    def fail_and_focus_up(self) -> bool:
        """
        Mark the current problem as failed and focus up
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_node:
            return False
            
        # Get the parent chain
        parent_chain = self.file_system.get_parent_chain(self.current_node)
        
        # If this is the root node, we're done
        if len(parent_chain) <= 1:
            # Mark the root node as FAILED
            self.current_node.status = ProblemStatus.FAILED
            self.file_system.update_files()
            self.finished = True
            return True
            
        # Mark the current node as FAILED
        self.current_node.status = ProblemStatus.FAILED
        
        # Get the parent node (second to last in the chain, as the last is the current node)
        parent_node = parent_chain[-2]
        
        # Set the parent to CURRENT
        parent_node.status = ProblemStatus.CURRENT
        
        # Update the current node
        self.activate_node(parent_node)
        
        # Update files
        self.file_system.update_files()
        
        return True

