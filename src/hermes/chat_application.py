from typing import Dict, List, Optional
import signal
from hermes.chat_models.base import ChatModel
from hermes.ui.chat_ui import ChatUI
from hermes.file_processors.base import FileProcessor
from hermes.prompt_formatters.base import PromptFormatter

class ChatApplication:
    def __init__(self, model: ChatModel, ui: ChatUI, file_processor: FileProcessor, prompt_formatter: PromptFormatter, special_command_prompts: Dict[str, str]):
        self.model = model
        self.ui = ui
        self.file_processor = file_processor
        self.prompt_formatter = prompt_formatter
        self.files: Dict[str, str] = {}
        self.special_command_prompts = special_command_prompts

    def set_files(self, files: Dict[str, str]):
        self.files = files

    def run(self, initial_prompt: Optional[str] = None, special_command: Optional[Dict[str, str]] = None):
        self.model.initialize()

        try:
            if not initial_prompt:
                if special_command:
                    if 'append' in special_command:
                        first_message = self.special_command_prompts['append'].format(file_name=special_command['append'])
                    elif 'update' in special_command:
                        first_message = self.special_command_prompts['update'].format(file_name=special_command['update'])
                else:
                    print("Chat started. Type 'exit', 'quit', or 'q' to end the conversation. Type '/clear' to clear the chat history.")
                    first_message = self.ui.get_user_input()
            else:
                first_message = initial_prompt


            if first_message.lower() in ['exit', 'quit', 'q']:
                return

            context = self.prompt_formatter.format_prompt(self.files, first_message, special_command)
            response = self.ui.display_response(self.model.send_message(context))

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
                    self.run(initial_prompt, special_command)
                    return

                self.ui.display_response(self.model.send_message(user_input))

        except KeyboardInterrupt:
            print("\nChat interrupted. Exiting gracefully...")

    def handle_special_command(self, special_command: Dict[str, str], content: str):
        if 'append' in special_command:
            self.file_processor.write_file(self.files[special_command['append']], "\n" + content, mode='a')
            self.ui.display_status(f"Content appended to {special_command['append']}")
        elif 'update' in special_command:
            self.file_processor.write_file(self.files[special_command['update']], content, mode='w')
            self.ui.display_status(f"File {special_command['update']} updated")

    def clear_chat(self):
        self.model.initialize()  # This will reset the chat history in the model
        self.ui.display_status("Chat history cleared.")
