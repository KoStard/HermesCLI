from typing import List, Dict, Any, Type
from hermes.prompt_builders.base import PromptBuilder

class HistoryBuilder:
    def __init__(self, context_prompt_builder_class: Type[PromptBuilder]):
        self.context_prompt_builder_class = context_prompt_builder_class
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
        context_prompt_builder = self.context_prompt_builder_class()
        last_user_message_index = -1

        # Find the index of the last user message
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]["role"] == "user":
                last_user_message_index = i
                break

        for i, message in enumerate(self.messages):
            if message["role"] == "context":
                if message["type"] == "text":
                    context_prompt_builder.add_text(message["content"], name=message["name"] or "Context")
                elif message["type"] == "file":
                    context_prompt_builder.add_file(message["content"], name=message["name"])
                elif message["type"] == "image":
                    context_prompt_builder.add_image(message["content"], name=message["name"])
            elif message["role"] == "user":
                context_content = context_prompt_builder.build_prompt()
                if context_content:
                    message["content"] = context_content + "\n\n" + message["content"]
                    context_prompt_builder = self.context_prompt_builder_class()  # Reset context for next user message
                compiled_messages.append(message)
                if i == last_user_message_index:
                    # Include all subsequent context with this user message
                    for j in range(i + 1, len(self.messages)):
                        if self.messages[j]["role"] == "context":
                            if self.messages[j]["type"] == "text":
                                context_prompt_builder.add_text(self.messages[j]["content"], name=self.messages[j]["name"] or "Context")
                            elif self.messages[j]["type"] == "file":
                                context_prompt_builder.add_file(self.messages[j]["content"], name=self.messages[j]["name"])
                            elif self.messages[j]["type"] == "image":
                                context_prompt_builder.add_image(self.messages[j]["content"], name=self.messages[j]["name"])
                    additional_context = context_prompt_builder.build_prompt()
                    if additional_context:
                        compiled_messages[-1]["content"] += "\n\n" + additional_context
            else:
                compiled_messages.append(message)

        return compiled_messages

    def clear_history(self):
        self.messages.clear()

    def get_last_messages(self, n: int) -> List[Dict[str, str]]:
        return [msg for msg in self.messages[-n:] if msg["role"] != "context"]
