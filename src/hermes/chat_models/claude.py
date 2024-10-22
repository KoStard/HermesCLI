from typing import Generator
from .base import ChatModel
from ..registry import register_model

@register_model(name=["claude-sonnet-3.5", "claude-sonnet-3.5-v2"], file_processor="default", prompt_builder="claude", config_key='ANTHROPIC')
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
            return 'claude-3-sonnet-20240229-v1:0'
        elif model_identifier == 'claude-sonnet-3.5-v2':
            return 'claude-3-5-sonnet-20241022'
        else:
            raise ValueError(f"Unsupported Claude model identifier: {model_identifier}")

    def send_history(self, messages) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model=self.model_id,
            messages=messages,
            max_tokens=1024
        ) as stream:
            for text in stream.text_stream:
                yield text
