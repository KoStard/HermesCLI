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

        # Use prompt_builder to build context content
        self.prompt_builder.erase()
        for item in self.context:
            if item["type"] == "text":
                self.prompt_builder.add_text(item["content"], name=item["name"] or "Context")
            elif item["type"] == "file":
                self.prompt_builder.add_file(item["content"], name=item["name"])
            elif item["type"] == "image":
                self.prompt_builder.add_image(item["content"], name=item["name"])

        context_content = self.prompt_builder.build_prompt()

        if context_content:
            messages.append({"role": "system", "content": context_content.strip()})

        # Add timeline messages
        messages.extend(self.timeline)

        return messages

    def clear_timeline(self):
        self.timeline.clear()

    def get_last_messages(self, n: int) -> List[Dict[str, str]]:
        return self.timeline[-n:]
