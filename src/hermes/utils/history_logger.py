"""
Goal:
- Implement a history logger class
- Will receive 2 types of calls
    - add_user_prompt(messages) -> The messages list that history_builder builds before sending to the LLM in ChatApplication
    - add_assistant_reply(text) -> The text of the assistant reply
- When initialised, will create a folder with the current date and time
- With each call, will create a new file in the folder, with the next incremental number with format "User {number}.txt" or "Assistant {number}.txt"
- The user file will contain the full user prompt, with all the messages (history + current). These will be combined as a single string, with newlines separating each message
- The assistant file will contain the only the recent assistant reply, as a single string
"""

import os
from datetime import datetime
from typing import List, Dict

class HistoryLogger:
    def __init__(self):
        self.log_folder = self._create_log_folder()
        self.counter = 0

    def _create_log_folder(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"/tmp/hermes/chat_logs_readable/hermes_history_{timestamp}"
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    def add_user_prompt(self, messages: List[Dict[str, str]]):
        self.counter += 1
        file_name = os.path.join(self.log_folder, f"{self.counter:03d}_User.txt")
        
        with open(file_name, 'w', encoding='utf-8') as f:
            for message in messages:
                if isinstance(message['content'], str):
                    f.write(message['content'])
                elif isinstance(message['content'], dict) and 'text' in message['content']:
                    f.write(message['content']['text'])
                else:
                    f.write(message['content'])
                f.write("\n\n")

    def add_assistant_reply(self, text: str):
        self.counter += 1
        file_name = os.path.join(self.log_folder, f"{self.counter:03d}_Assistant.txt")
        
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(text)
