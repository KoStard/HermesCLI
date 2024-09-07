from typing import Dict, List, Optional
import signal, sys
from hermes.chat_models.base import ChatModel
from hermes.context_orchestrator import ContextOrchestrator
from hermes.prompt_builders.base import PromptBuilder
from hermes.ui.chat_ui import ChatUI
from hermes.file_processors.base import FileProcessor
from hermes.utils.file_utils import process_file_name

class ChatApplication:
    def __init__(self, model: ChatModel, ui: ChatUI, file_processor: FileProcessor, prompt_builder: PromptBuilder, special_command_prompts: Dict[str, str], context_orchestrator: ContextOrchestrator):
        self.model = model
        self.ui = ui
        self.file_processor = file_processor
        self.prompt_builder = prompt_builder
        self.special_command_prompts = special_command_prompts
        self.context_orchestrator = context_orchestrator

    def make_first_request(self, initial_prompt: Optional[str] = None, special_command: Optional[Dict[str, str]] = None):
        self.prompt_builder.erase()
        self.context_orchestrator.build_prompt(self.prompt_builder)
        if initial_prompt:
            self.prompt_builder.add_text(initial_prompt)
        if 'append' in special_command:
            self.prompt_builder.add_text(self.special_command_prompts['append'].format(file_name=special_command['append']))
        elif 'update' in special_command:
            self.prompt_builder.add_text(self.special_command_prompts['update'].format(file_name=special_command['update']))
        elif not initial_prompt:
            print("Chat started. Type 'exit', 'quit', or 'q' to end the conversation. Type '/clear' to clear the chat history.")
            while True:
                text = self.ui.get_user_input()
                user_input_lower = text.lower()

                if user_input_lower in ['exit', 'quit', 'q']:
                    return
                elif user_input_lower == '/clear':
                    self.clear_chat()
                    continue
                else:
                    self.prompt_builder.add_text(text)
                    break

        context = self.prompt_builder.build_prompt()
        response = self.ui.display_response(self.model.send_message(context))
        return response

    def run(self, initial_prompt: Optional[str] = None, special_command: Optional[Dict[str, str]] = None):
        if not special_command:
            special_command = {}
        self.model.initialize()

        # Check if input is coming from a pipe
        if not sys.stdin.isatty():
            self.context_orchestrator.build_prompt(self.prompt_builder)
            if initial_prompt:
                user_input = initial_prompt
            else:
                user_input = sys.stdin.read().strip()

            if user_input:
                self.prompt_builder.add_text(user_input)
                if 'append' in special_command:
                    self.prompt_builder.add_text(self.special_command_prompts['append'].format(file_name=process_file_name(special_command['append'])))
                elif 'update' in special_command:
                    self.prompt_builder.add_text(self.special_command_prompts['update'].format(file_name=process_file_name(special_command['update'])))
                context = self.prompt_builder.build_prompt()
                response = self.ui.display_response(self.model.send_message(context))
                if special_command:
                    self.handle_special_command(special_command, response)
            return

        # Interactive mode
        try:
            response = self.make_first_request(initial_prompt, special_command)

            if special_command:
                self.handle_special_command(special_command, response)
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

                self.ui.display_response(self.model.send_message(user_input))

        except KeyboardInterrupt:
            print("\nChat interrupted. Exiting gracefully...")

    def handle_special_command(self, special_command: Dict[str, str], content: str):
        if 'append' in special_command:
            self.file_processor.write_file(special_command['append'], "\n" + content, mode='a')
            self.ui.display_status(f"Content appended to {special_command['append']}")
        elif 'update' in special_command:
            self.file_processor.write_file(special_command['update'], content, mode='w')
            self.ui.display_status(f"File {special_command['update']} updated")

    def clear_chat(self):
        self.model.initialize()
        self.ui.display_status("Chat history cleared.")

