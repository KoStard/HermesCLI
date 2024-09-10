from typing import List, Dict, Any
from hermes.prompt_builders.base import PromptBuilder

class HistoryBuilder:
    def __init__(self, prompt_builder: PromptBuilder):
        self.prompt_builder = prompt_builder
        self.messages: List[Dict[str, Any]] = []

    def add_context(self, content_type: str, content: str, name: str = None):
        self.messages.append({
            "role": "context",
            "type": content_type,
            "content": content,
            "name": name
        })

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content
        })

    def build_messages(self) -> List[Dict[str, str]]:
        compiled_messages = []
        context_buffer = ""
        last_user_message_index = -1

        # Find the index of the last user message
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]["role"] == "user":
                last_user_message_index = i
                break

        for i, message in enumerate(self.messages):
            if message["role"] == "context":
                if message["type"] == "text":
                    context_buffer += f"{message['name'] or 'Context'}: {message['content']}\n\n"
                elif message["type"] == "file":
                    context_buffer += f"File {message['name']}: {message['content']}\n\n"
                elif message["type"] == "image":
                    context_buffer += f"Image {message['name']} is attached.\n\n"
            elif message["role"] == "user":
                if context_buffer:
                    message["content"] = context_buffer + message["content"]
                    context_buffer = ""
                compiled_messages.append(message)
                if i == last_user_message_index:
                    # Include all subsequent context with this user message
                    for j in range(i + 1, len(self.messages)):
                        if self.messages[j]["role"] == "context":
                            if self.messages[j]["type"] == "text":
                                compiled_messages[-1]["content"] += f"\n\n{self.messages[j]['name'] or 'Context'}: {self.messages[j]['content']}"
                            elif self.messages[j]["type"] == "file":
                                compiled_messages[-1]["content"] += f"\n\nFile {self.messages[j]['name']}: {self.messages[j]['content']}"
                            elif self.messages[j]["type"] == "image":
                                compiled_messages[-1]["content"] += f"\n\nImage {self.messages[j]['name']} is attached."
            else:
                compiled_messages.append(message)

        return compiled_messages

    def clear_history(self):
        self.messages.clear()

    def get_last_messages(self, n: int) -> List[Dict[str, str]]:
        return [msg for msg in self.messages[-n:] if msg["role"] != "context"]
