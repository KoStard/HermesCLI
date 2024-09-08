from typing import Dict, List, Optional
import sys
from hermes.chat_models.base import ChatModel
from hermes.context_orchestrator import ContextOrchestrator
from hermes.prompt_builders.base import PromptBuilder
from hermes.ui.chat_ui import ChatUI
from hermes.utils import file_utils

class ChatApplication:
    def __init__(self, model: ChatModel, ui: ChatUI, prompt_builder: PromptBuilder, special_command_prompts: Dict[str, str], context_orchestrator: ContextOrchestrator):
        self.model = model
        self.ui = ui
        self.prompt_builder = prompt_builder
        self.special_command_prompts = special_command_prompts
        self.context_orchestrator = context_orchestrator

    def run(self, initial_prompt: Optional[str] = None, special_command: Optional[Dict[str, str]] = None):
        if not special_command:
            special_command = {}
        self.model.initialize()

        # Check if input or output is coming from a pipe
        is_input_piped = not sys.stdin.isatty()
        is_output_piped = not sys.stdout.isatty()
        
        if is_input_piped or is_output_piped:
            self.handle_non_interactive_input_output(initial_prompt, special_command, is_input_piped, is_output_piped)
            return

        # Interactive mode
        try:
            self.handle_interactive_mode(initial_prompt, special_command)
        except KeyboardInterrupt:
            print("\nChat interrupted. Exiting gracefully...")
    
    def handle_interactive_mode(self, initial_prompt, special_command):
        if not self.make_first_request(initial_prompt, special_command):
            return
        
        while True:
            user_input = self.ui.get_user_input()
            user_input_lower = user_input.lower()

            if user_input_lower in ['exit', 'quit', 'q']:
                return
            elif user_input_lower == '/clear':
                self.clear_chat()
                self.make_first_request(initial_prompt, special_command)
                continue

            self.send_message_and_print_output(user_input)
    
    def make_first_request(self, initial_prompt: Optional[str] = None, special_command: Optional[Dict[str, str]] = None):
        self.prompt_builder.erase()
        self.context_orchestrator.add_to_prompt(self.prompt_builder)
        if initial_prompt:
            self.prompt_builder.add_text(initial_prompt)
        if not self.add_special_command_to_prompt(special_command) and not initial_prompt:
            print("Chat started. Type 'exit', 'quit', or 'q' to end the conversation. Type '/clear' to clear the chat history.")
            while True:
                text = self.ui.get_user_input()
                user_input_lower = text.lower()

                if user_input_lower in ['exit', 'quit', 'q']:
                    return False
                elif user_input_lower == '/clear':
                    self.clear_chat()
                    continue
                else:
                    self.prompt_builder.add_text(text)
                    break

        message = self.prompt_builder.build_prompt()
        response = self.send_message_and_print_output(message)
        
        if special_command:
            self.apply_special_command(special_command, response)
            return False
        return True
    
    def handle_non_interactive_input_output(self, initial_prompt, special_command, is_input_piped, is_output_piped):
        self.context_orchestrator.add_to_prompt(self.prompt_builder)

        if initial_prompt:
            self.prompt_builder.add_text(initial_prompt)
        if is_input_piped:
            self.prompt_builder.add_text(sys.stdin.read().strip())
        elif not initial_prompt:
            self.prompt_builder.add_text(self.ui.get_user_input())
        self.add_special_command_to_prompt(special_command)
        
        message = self.prompt_builder.build_prompt()
        response = self.send_message_and_print_output(message)
        
        if special_command:
            if is_output_piped:
                raise Exception("Special command not supported for non-interactive output")
            self.apply_special_command(special_command, response)
    
    def add_special_command_to_prompt(self, special_command: Dict[str, str]):
        if 'append' in special_command:
            self.prompt_builder.add_text(self.special_command_prompts['append'].format(file_name=file_utils.process_file_name(special_command['append'])))
        elif 'update' in special_command:
            self.prompt_builder.add_text(self.special_command_prompts['update'].format(file_name=file_utils.process_file_name(special_command['update'])))
        else:
            return False
        return True

    def apply_special_command(self, special_command: Dict[str, str], content: str):
        if 'append' in special_command:
            file_utils.write_file(special_command['append'], "\n" + content, mode='a')
            self.ui.display_status(f"Content appended to {special_command['append']}")
        elif 'update' in special_command:
            file_utils.write_file(special_command['update'], content, mode='w')
            self.ui.display_status(f"File {special_command['update']} updated")

    def send_message_and_print_output(self, user_input):
        try:
            response = self.ui.display_response(self.model.send_message(user_input))
            return response
        except KeyboardInterrupt:
            print()
            self.ui.display_status(f"Interrupted...")

    def clear_chat(self):
        self.model.initialize()
        self.ui.display_status("Chat history cleared.")

