from typing import Generator

from hermes.interface.assistant.llm_response_types import TextLLMResponse, ThinkingLLMResponse
from hermes.interface.assistant.prompt_builder.simple_prompt_builder import SimplePromptBuilderFactory
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.openai import OpenAIRequestBuilder
from .base import ChatModel

class OpenAIModel(ChatModel):
    def initialize(self):
        self.request_builder = OpenAIRequestBuilder(self.model_tag, self.notifications_printer, SimplePromptBuilderFactory())

        import openai

        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for OpenAI model")
        base_url = self.config.get("base_url", "https://api.openai.com/v1")
        self.model = self.config.get("model", "gpt-4o")
        self.client = openai.Client(api_key=api_key, base_url=base_url)

    def send_request(self, request: any) -> Generator[str, None, None]:
        import openai
        try:
            stream = self.client.chat.completions.create(
                **request
            )
        except openai.AuthenticationError as e:
            raise Exception("Authentication failed. Please check your API key.", e)
        for chunk in stream:
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content is not None:
                yield ThinkingLLMResponse(chunk.choices[0].delta.reasoning_content)
            if chunk.choices[0].delta.content is not None:
                yield TextLLMResponse(chunk.choices[0].delta.content)

    @staticmethod
    def get_provider() -> str:
        return 'OPENAI'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        return ["gpt-4o"]
    
    def get_request_builder(self) -> RequestBuilder:
        return self.request_builder

    def set_thinking_level(self, level: str):
        if hasattr(self.request_builder, "set_reasoning_effort"):
            self.request_builder.set_reasoning_effort(level)
