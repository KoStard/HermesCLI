from typing import Generator
from .base import ChatModel
from ..registry import register_model

@register_model(name=["claude-sonnet-3.5", "claude-sonnet-3.5-v2", "claude-heiku-3.5"], file_processor="default", prompt_builder="claude", config_key='ANTHROPIC')
class ClaudeModel(ChatModel):
    def initialize(self):
        import anthropic
        
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Claude model")
        self.client = anthropic.Anthropic(api_key=api_key)
        model_identifier = self.config["model_identifier"]
        self.model_id = self.get_model_id(model_identifier)

    def get_model_id(self, model_identifier):
        if model_identifier == 'claude-sonnet-3.5':
            return 'claude-3-5-sonnet-20240620'
        elif model_identifier == 'claude-sonnet-3.5-v2':
            return 'claude-3-5-sonnet-20241022'
        elif model_identifier == 'claude-heiku-3.5':
            return 'claude-3-5-haiku-20241022'
        else:
            raise ValueError(f"Unsupported Claude model identifier: {model_identifier}")

    def send_history(self, messages) -> Generator[str, None, None]:
        system_message = None
        if messages[0]['role'] == 'system':
            system_message = '\n'.join([m.get('text') for m in messages[0]['content'] if m.get('text')])
            messages = messages[1:]
        extra_kwargs = {}
        if system_message:
            extra_kwargs['system'] = system_message
        with self.client.messages.stream(
            model=self.model_id,
            messages=messages,
            max_tokens=4096,
            **extra_kwargs
        ) as stream:
            for text in stream.text_stream:
                yield text
