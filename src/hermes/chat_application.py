from typing import Optional, Dict, Any
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

    def run(self, initial_content: Optional[Any] = None, special_command: Optional[Dict[str, str]] = None):
        self.model.initialize()
        
        if initial_content and special_command:
            response = self.ui.display_response(self.model.send_message(initial_content))
            if 'append' in special_command:
                self.append_to_file(special_command['append'], response)
            elif 'update' in special_command:
                self.update_file(special_command['update'], response)
            return

        print("Chat started. Type 'exit', 'quit', or 'q' to end the conversation.")
        
        if initial_content:
            self.ui.display_response(self.model.send_message(initial_content))

        while True:
            user_input = self.ui.get_user_input()
            used_input_lw = user_input.lower()
            
            if used_input_lw in ['exit', 'quit', 'q']:
                return

            self.ui.display_response(self.model.send_message(user_input))

    def append_to_file(self, file_path: str, content: str):
        self.file_processor.write_file(file_path, "\n" + content, mode='a')
        self.ui.display_status(f"Content appended to {file_path}")

    def update_file(self, file_path: str, content: str):
        self.file_processor.write_file(file_path, content, mode='w')
        self.ui.display_status(f"File {file_path} updated")
