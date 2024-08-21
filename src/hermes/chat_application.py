from typing import Dict, List, Optional
from hermes.chat_models.base import ChatModel
from hermes.ui.chat_ui import ChatUI
from hermes.file_processors.base import FileProcessor
from hermes.prompt_formatters.base import PromptFormatter

class ChatApplication:
    def __init__(self, model: ChatModel, ui: ChatUI, file_processor: FileProcessor, prompt_formatter: PromptFormatter):
        self.model = model
        self.ui = ui
        self.file_processor = file_processor
        self.prompt_formatter = prompt_formatter
        self.files: Dict[str, str] = {}

    def set_files(self, files: Dict[str, str]):
        self.files = files

    def run(self, initial_prompt: Optional[str] = None, special_command: Optional[Dict[str, str]] = None):
        self.model.initialize()
        
        print("Chat started. Type 'exit', 'quit', or 'q' to end the conversation.")

        first_message = initial_prompt if initial_prompt else self.ui.get_user_input()
        
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

            self.ui.display_response(self.model.send_message(user_input))

    def handle_special_command(self, special_command: Dict[str, str], content: str):
        if 'append' in special_command:
            self.file_processor.write_file(special_command['append'], "\n" + content, mode='a')
            self.ui.display_status(f"Content appended to {special_command['append']}")
        elif 'update' in special_command:
            self.file_processor.write_file(special_command['update'], content, mode='w')
            self.ui.display_status(f"File {special_command['update']} updated")
