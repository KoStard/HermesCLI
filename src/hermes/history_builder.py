import logging
import json
from typing import Dict, List, Type

from hermes.chat_ui import ChatUI
from hermes.context_providers.base import ContextProvider, LiveContextProvider
from hermes.file_processors.base import FileProcessor
from hermes.prompt_builders.base import PromptBuilder
from itertools import groupby
from hermes.chunks import BaseChunk, AssistantChunk, UserTextChunk, UserContextChunk

# Set up logging
logger = logging.getLogger(__name__)


"""
New vision definition:
- History needs additional non-content chunks, maybe called flags or markers
- Likely we'll get rid of the idea of active and passive chunks
- We should capture the user intent to finish their turn, same with the AI
- Same should be used for the AI, this will be ground work for further agentic behaviours
- One multiline input is considered one turn. The user should also be able to "start" and "stop" the turns more explicitely
- The user should be able to enter multiple turns in one multiline input with special command /turn or something with similar name (TBD).
- This then should be used to determine when the turn is finished and if additional user input is necessary
- After /clear the flags should be cleared and regenerated.
- There should be logic at the beginning of the chat to check if user has shows intent to directly ask for the LLM input or not - based on CLI inputs
"""


class HistoryBuilder:
    def __init__(
        self, 
        prompt_builder_class: Type[PromptBuilder], 
        file_processor: FileProcessor, 
        command_keys_map: Dict[str, Type[ContextProvider]]
    ):
        self.prompt_builder_class = prompt_builder_class
        self.file_processor = file_processor
        self.command_keys_map = command_keys_map
        self.live_context_providers: List[LiveContextProvider] = []
        self.chunks: List[BaseChunk] = []

    def lacks_user_input(self) -> bool:
        for chunk in reversed(self.chunks):
            if (chunk.author == "user" and 
                chunk.active and 
                not getattr(chunk, 'override_passive', False)):
                return False
            if chunk.author == "assistant":
                return True
        return True

    def force_need_for_user_input(self):
        for chunk in reversed(self.chunks):
            if chunk.author == "user" and chunk.active:
                setattr(chunk, 'override_passive', True)
            if chunk.author == "assistant":
                return

    def add_assistant_reply(self, content: str):
        self.chunks.append(AssistantChunk(text=content))

    def add_user_input(self, content: str, active=False, permanent=False):
        self.chunks.append(UserTextChunk(text=content, active=active, permanent=permanent))

    def add_context(self, context_provider: ContextProvider, active=False, permanent=False):
        self.chunks.append(
            UserContextChunk(
                context_provider=context_provider,
                active=active,
                permanent=permanent
            )
        )
        if isinstance(context_provider, LiveContextProvider):
            self.live_context_providers.append(context_provider)
    
    def add_live_context_provider_snapshots(self):
        for provider in self.live_context_providers:
            for snapshot_provider in provider.get_live_diff_snapshot():
                self.add_context(snapshot_provider, permanent=False)

    def _get_prompt_builder(self, author: str, do_introduction: bool = False):
        return self.prompt_builder_class(self.file_processor, author, do_introduction)

    def build_messages(self) -> List[Dict[str, str]]:
        compiled_messages = []
        is_first_user_message = True
        instructions_messages = set()

        chunk_groups = groupby(self.chunks, lambda x: x.author)
        for author, group in chunk_groups:
            prompt_builder = self._get_prompt_builder(author, is_first_user_message and author == "user")
            if author == "user":
                is_first_user_message = False
            for chunk in group:
                if isinstance(chunk, UserContextChunk):
                    chunk.context_provider.add_to_prompt(prompt_builder)
                    instructions = chunk.context_provider.get_instructions()
                    if instructions:
                        instructions_messages.add(instructions)
                else:
                    prompt_builder.add_text(chunk.text)
            compiled_messages.append(
                {
                    "role": author,
                    "content": prompt_builder.build_prompt(),
                }
            )
        
        instructions_prompt_builder = self._get_prompt_builder("system", False)
        for instruction in instructions_messages:
            if instruction:
                instructions_prompt_builder.add_text(instruction)
        if instructions_messages:
            compiled_messages.insert(0, {
                "role": "system",
                "content": instructions_prompt_builder.build_prompt(),
            })
        
        return compiled_messages

    def clear_regular_history(self):
        self.chunks = [chunk for chunk in self.chunks if chunk.permanent]

    def run_pending_actions(self, executor, ui: ChatUI):
        chunks = self._get_recent_action_chunks_to_run()
        for chunk in chunks:
            status = executor(chunk.context_provider)
            chunk.has_acted = True
            if status != None:
                ui.display_status(status)

    def _get_recent_action_chunks_to_run(self):
        reversed_chunk_groups = groupby(self.chunks[::-1], lambda x: x.author)
        found_assistant = False
        for author, group in reversed_chunk_groups:
            if found_assistant and author == "user":
                return [
                    chunk
                    for chunk in group
                    if isinstance(chunk, UserContextChunk)
                    and chunk.is_action
                    and not getattr(chunk, 'has_acted', False)
                ]
            if author == "assistant":
                found_assistant = True
        return []

    def get_recent_llm_response(self):
        reversed_chunk_groups = groupby(self.chunks[::-1], lambda x: x.author)
        for author, group in reversed_chunk_groups:
            if author == "assistant":
                return next((chunk.text for chunk in group if isinstance(chunk, AssistantChunk)), None)
        return None

    def save_history(self, file_path: str):
        serialized_chunks = []
        for chunk in self.chunks:
            if isinstance(chunk, AssistantChunk):
                serialized_chunks.append({
                    'author': chunk.author,
                    'text': chunk.text,
                    'permanent': chunk.permanent
                })
            elif isinstance(chunk, UserTextChunk):
                serialized_chunks.append({
                    'author': chunk.author,
                    'text': chunk.text,
                    'active': chunk.active,
                    'permanent': chunk.permanent
                })
            elif isinstance(chunk, UserContextChunk):
                keys = chunk.context_provider.get_command_key()
                if not isinstance(keys, list):
                    keys = [keys]
                serialized_chunks.append({
                    'author': chunk.author,
                    'context_provider': chunk.context_provider.serialize(),
                    'context_provider_keys': keys,
                    'active': chunk.active,
                    'is_action': chunk.is_action,
                    'has_acted': chunk.has_acted,
                    'permanent': chunk.permanent
                })

        with open(file_path, 'w') as f:
            json.dump(serialized_chunks, f, indent=2)

    def load_history(self, file_path: str):
        with open(file_path, 'r') as f:
            serialized_chunks = json.load(f)

        self.chunks = []
        for serialized_chunk in serialized_chunks:
            if serialized_chunk['author'] == 'assistant':
                self.chunks.append(AssistantChunk(
                    text=serialized_chunk['text'],
                    permanent=serialized_chunk.get('permanent', False)
                ))
            elif serialized_chunk['author'] == 'user':
                if 'context_provider' in serialized_chunk:
                    provider_key = serialized_chunk['context_provider_keys'][0]
                    provider_class = self.command_keys_map.get(provider_key)
                    if provider_class:
                        provider_instance = provider_class()
                        try:
                            provider_instance.deserialize(serialized_chunk['context_provider'])
                            context_chunk = UserContextChunk(
                                context_provider=provider_instance,
                                active=serialized_chunk['active'],
                                permanent=serialized_chunk.get('permanent', False)
                            )
                            context_chunk.has_acted = serialized_chunk.get('has_acted', False)
                            self.chunks.append(context_chunk)
                        except Exception as e:
                            logger.warning(f"Failed to deserialize context provider {provider_key}: {str(e)}")
                    else:
                        logger.warning(f"Unknown context provider: {provider_key}")
                else:
                    self.chunks.append(UserTextChunk(
                        text=serialized_chunk['text'],
                        active=serialized_chunk['active'],
                        permanent=serialized_chunk.get('permanent', False)
                    ))
