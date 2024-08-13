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

    def run(self, initial_content: any, special_command: Optional[Dict[str, str]] = None, ask_for_user_prompt: bool = False):
        if special_command:
            self.model.initialize()
            response = self.ui.display_response(self.model.send_message(initial_content))
            if 'append' in special_command:
                self.append_to_file(special_command['append'], response)
            elif 'update' in special_command:
                self.update_file(special_command['update'], response)
        else:
            latest_input = ""
            print("Chat started. Type 'exit', 'quit', or 'q' to end the conversation.")
            while True:
                self.model.initialize()
                current_initial_content = initial_content
                
                if not latest_input and ask_for_user_prompt:
                    latest_input = self.ui.get_user_input()
                
                if latest_input:
                    current_initial_content = self.prompt_formatter.add_content(initial_content, latest_input)

                self.ui.display_response(self.model.send_message(current_initial_content))
                
                while True:
                    user_input = self.ui.get_user_input()
                    used_input_lw = user_input.lower()
                    if used_input_lw.startswith('/new') or used_input_lw.startswith('/n'):
                        latest_input = ' '.join(user_input.split(' ')[1:])
                        break
                    if used_input_lw in ['exit', 'quit', 'q']:
                        return

                    self.ui.display_response(self.model.send_message(user_input))

    def append_to_file(self, file_path: str, content: str):
        self.file_processor.write_file(file_path, "\n" + content, mode='a')
        self.ui.display_status(f"Content appended to {file_path}")

    def update_file(self, file_path: str, content: str):
        self.file_processor.write_file(file_path, content, mode='w')
        self.ui.display_status(f"File {file_path} updated")
