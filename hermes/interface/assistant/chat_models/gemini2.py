from typing import Generator
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Part, Content

from hermes.interface.assistant.llm_response_types import BaseLLMResponse, TextLLMResponse, ThinkingLLMResponse
from hermes.interface.assistant.prompt_builder.simple_prompt_builder import SimplePromptBuilderFactory
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.gemini2 import Gemini2RequestBuilder
from .base import ChatModel

class Gemini2Model(ChatModel):
    def initialize(self):
        from google import genai
        
        self.request_builder = Gemini2RequestBuilder(self.model_tag, self.notifications_printer, SimplePromptBuilderFactory())

        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Gemini model")
        
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
        self.google_search_tool = Tool(google_search=GoogleSearch())

    @property
    def _supports_thinking(self) -> bool:
        return 'thinking' in self.model_tag

    def send_request(self, request: any) -> Generator[str, None, None]:
        response = self.client.models.generate_content(
            model=request['model_name'],
            contents=request['contents'],
            config=GenerateContentConfig(
                response_modalities=["TEXT"],
                tools=request['tools'],
            )
        )
        
        has_finished_thinking = False if self._supports_thinking else True
        
        for part in response.candidates[0].content.parts:
            yield from self._convert_to_llm_response(
                self._handle_part(part), 
                is_thinking=not has_finished_thinking
            )
            
            # Handle thinking state transitions
            if hasattr(part, 'thought') and part.thought:
                has_finished_thinking = False
            else:
                has_finished_thinking = True

    def _handle_part(self, part) -> Generator[str, None, None]:
        if hasattr(part, 'text'):
            yield part.text
            return

        if hasattr(part, 'executable_code'):
            language = part.executable_code.language or ""
            yield f"```{language}\n{part.executable_code.code}\n```"
            return

        if hasattr(part, 'code_execution_result'):
            yield f"```\n{part.code_execution_result.output}\n```"
            return

        yield str(part)

    def _convert_to_llm_response(self, responses: Generator[str, None, None], is_thinking: bool) -> Generator[BaseLLMResponse, None, None]:
        for response in responses:
            if is_thinking:
                yield ThinkingLLMResponse(response)
            else:
                yield TextLLMResponse(response)

    @staticmethod
    def get_provider() -> str:
        return 'GEMINI'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        models = [
            'gemini-2.0-flash-exp',
            'gemini-2.0-flash-exp/grounded',
            'gemini-2.0-flash-thinking-exp-1219',
        ]
        return models

    def get_request_builder(self) -> RequestBuilder:
        return self.request_builder
