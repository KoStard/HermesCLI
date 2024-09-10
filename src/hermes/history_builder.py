from typing import List, Dict, Any, Type
from hermes.file_processors.base import FileProcessor
from hermes.prompt_builders.base import PromptBuilder
from hermes.context_providers.base import ContextProvider

class HistoryBuilder:
    def __init__(self, context_prompt_builder_class: Type[PromptBuilder], file_processor: FileProcessor, context_providers: List[ContextProvider]):
        self.context_prompt_builder_class = context_prompt_builder_class
        self.file_processor = file_processor
        self.messages: List[Dict[str, Any]] = []
        self.context_providers = context_providers

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content
        })

    def add_context(self, context_provider: ContextProvider):
        self.context_providers.append(context_provider)

    def build_messages(self) -> List[Dict[str, str]]:
        compiled_messages = []
        context_prompt_builder = self.context_prompt_builder_class(self.file_processor)
        last_user_message_index = -1

        # Find the index of the last user message
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]["role"] == "user":
                last_user_message_index = i
                break
        if last_user_message_index < len(self.messages) - 1:
            self.messages = self.messages[:last_user_message_index+1]
            print(f"Truncated messages: {self.messages} because it contains non-user messages after the last user message.")

        # Add context from providers
        for provider in self.context_providers:
            provider.add_to_prompt(context_prompt_builder)

        for i, message in enumerate(self.messages):
            if message["role"] == "user":
                context_prompt_builder.add_text(message["content"])
                message_content = context_prompt_builder.build_prompt()
                context_prompt_builder = self.context_prompt_builder_class(self.file_processor)  # Reset context for next user message
                compiled_messages.append({
                    **message,
                    'content': message_content
                })
            else:
                compiled_messages.append(message)

        return compiled_messages

    def clear_regular_history(self):
        self.messages = []
    
    def pop_message(self):
        return self.messages.pop()
