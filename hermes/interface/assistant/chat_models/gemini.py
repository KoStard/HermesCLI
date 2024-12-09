from typing import Generator

from hermes_beta.interface.assistant.prompt_builder.simple_prompt_builder import SimplePromptBuilderFactory
from hermes_beta.interface.assistant.request_builder.base import RequestBuilder
from hermes_beta.interface.assistant.request_builder.gemini import GeminiRequestBuilder
from .base import ChatModel

class GeminiModel(ChatModel):
    def initialize(self):
        import google.generativeai as genai

        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Gemini model")
        genai.configure(api_key=api_key)

    def send_request(self, request: any) -> Generator[str, None, None]:
        import google.generativeai as genai

        model = genai.GenerativeModel(**request['model_kwargs'])

        chat = model.start_chat(history=request['history'])
        response = chat.send_message(**request['message'])
        for chunk in response:
            yield chunk.text

    @staticmethod
    def get_provider() -> str:
        return 'GEMINI'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        models = [
            'gemini-1.5-pro-exp-0801',
            'gemini-1.5-pro-exp-0827',
            'gemini-exp-1206',
            'gemini-1.5-pro-002',
            'gemini-1.5-flash-002',
            'gemini-exp-1114',
            'gemini-1.5-pro-002/grounded',
        ]
        return models

    def get_request_builder(self) -> RequestBuilder:
        return GeminiRequestBuilder(self.model_tag, self.notifications_printer, SimplePromptBuilderFactory())
