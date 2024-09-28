import logging
from typing import Any, Dict, List, Type

from hermes.chat_ui import ChatUI
from hermes.context_providers.base import ContextProvider
from hermes.file_processors.base import FileProcessor
from hermes.prompt_builders.base import PromptBuilder
from itertools import groupby

# Set up logging
logger = logging.getLogger(__name__)


class HistoryBuilder:
    def __init__(
        self, prompt_builder_class: Type[PromptBuilder], file_processor: FileProcessor
    ):
        self.prompt_builder_class = prompt_builder_class
        self.file_processor = file_processor

        # New format
        # {'author': 'assistant', 'text': text}
        # {'author': 'user', 'context_provider': ContextProviderInstance, 'active': bool}
        # {'author': 'user', 'text': text, 'active': bool}
        # active represents if it was an active input from the user that counts as their consent to send the message
        # or just some passive collected chunks that still requires user input
        self.chunks = []

    def requires_user_input(self) -> bool:
        for chunk in reversed(self.chunks):
            if chunk["author"] == "user" and chunk.get("active", False):
                return False  # We already have a user input
            if chunk["author"] == "assistant":
                return True
        return True

    def add_assistant_reply(self, content: str):
        self.chunks.append({"author": "assistant", "text": content})

    def add_user_input(self, content: str, active=False, permanent=False):
        self.chunks.append({"author": "user", "text": content, "active": active, "permanent": permanent})

    def add_context(self, context_provider: ContextProvider, active=False, permanent=False):
        self.chunks.append(
            {"author": "user", 
             "context_provider": context_provider, 
             "active": active,
             # Saving if the context provider is an action or not
             "is_action":  context_provider.is_action(),
             "has_acted": False,
             "permanent": permanent}
        )

    def _get_prompt_builder(self):
        return self.prompt_builder_class(self.file_processor)

    def build_messages(self) -> List[Dict[str, str]]:
        compiled_messages = []

        chunk_groups = groupby(self.chunks, lambda x: x["author"])
        for author, group in chunk_groups:
            prompt_builder = self._get_prompt_builder()
            for chunk in group:
                if "context_provider" in chunk:
                    chunk["context_provider"].add_to_prompt(prompt_builder)
                else:
                    prompt_builder.add_text(chunk["text"])
            compiled_messages.append(
                {
                    "role": author,
                    "content": prompt_builder.build_prompt(),
                }
            )
        return compiled_messages

    def clear_regular_history(self):
        self.chunks = [chunk for chunk in self.chunks if chunk.get('permanent', False)]

    def run_pending_actions(self, executor, ui: ChatUI):
        chunks = self._get_recent_action_chunks_to_run()
        for chunk in chunks:
            status = executor(chunk["context_provider"])
            chunk['has_acted'] = True
            if status != None:
                ui.display_status(status)

    def _get_recent_action_chunks_to_run(self):
        reversed_chunk_groups = groupby(self.chunks[::-1], lambda x: x["author"])
        found_assistant = False
        for author, group in reversed_chunk_groups:
            if found_assistant and author == "user":
                return [
                    chunk
                    for chunk in group
                    if "context_provider" in chunk
                    and chunk.get('is_action', False)
                    and not chunk.get('has_acted', False)
                ]
            if author == "assistant":
                found_assistant = True
        return []

    def get_recent_llm_response(self):
        reversed_chunk_groups = groupby(self.chunks[::-1], lambda x: x["author"])
        for author, group in reversed_chunk_groups:
            if author == "assistant":
                return next((chunk["text"] for chunk in group if "text" in chunk), None)
        return None
