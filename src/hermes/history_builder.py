from typing import List, Dict, Any
from hermes.prompt_builders.base import PromptBuilder

class HistoryBuilder:
    def __init__(self, prompt_builder: PromptBuilder):
        self.prompt_builder = prompt_builder
        self.context: List[Dict[str, Any]] = []
        self.timeline: List[Dict[str, str]] = []

    def add_context(self, content_type: str, content: str, name: str = None):
        self.context.append({
            "type": content_type,
            "content": content,
            "name": name
        })

    def add_message(self, role: str, content: str):
        self.timeline.append({
            "role": role,
            "content": content
        })

    def build_messages(self) -> List[Dict[str, str]]:
        messages = []

        # Add context as a system message
        context_content = ""
        for item in self.context:
            if item["type"] == "text":
                context_content += f"{item['name'] or 'Context'}: {item['content']}\n\n"
            elif item["type"] == "file":
                context_content += f"File {item['name']}: {item['content']}\n\n"
            elif item["type"] == "image":
                context_content += f"Image {item['name']} is attached.\n\n"

        if context_content:
            messages.append({"role": "system", "content": context_content.strip()})

        # Add timeline messages
        messages.extend(self.timeline)

        return messages

    def clear_timeline(self):
        self.timeline.clear()

    def get_last_messages(self, n: int) -> List[Dict[str, str]]:
        return self.timeline[-n:]
