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

        for message in self.messages:
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
            else:
                compiled_messages.append(message)

        # If there's any remaining context, add it as a system message
        if context_buffer:
            compiled_messages.insert(0, {"role": "system", "content": context_buffer.strip()})

        return compiled_messages

    def clear_history(self):
        self.messages.clear()

    def get_last_messages(self, n: int) -> List[Dict[str, str]]:
        return [msg for msg in self.messages[-n:] if msg["role"] != "context"]
