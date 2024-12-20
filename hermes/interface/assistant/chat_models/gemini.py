from typing import Generator

from hermes.interface.assistant.prompt_builder.simple_prompt_builder import SimplePromptBuilderFactory
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.gemini import GeminiRequestBuilder
from .base import ChatModel

class GeminiModel(ChatModel):
    def initialize(self):
        import google.generativeai as genai

        self.request_builder = GeminiRequestBuilder(self.model_tag, self.notifications_printer, SimplePromptBuilderFactory())

        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Gemini model")
        genai.configure(api_key=api_key)

    @property
    def _supports_thinking(self) -> bool:
        return 'thinking' in self.model_tag

    def send_request(self, request: any) -> Generator[str, None, None]:
        import google.generativeai as genai

        model = genai.GenerativeModel(**request['model_kwargs'])

        chat = model.start_chat(history=request['history'])
        response = chat.send_message(**request['message'])
        has_finished_thinking = False if self._supports_thinking else True
        for chunk in response:
            parts = chunk.candidates[0].content.parts

            yield from self._handle_part(parts[0])
            if len(parts) == 2:
                if not has_finished_thinking:
                    # Here I could do something, as I see the middle between the thinking and the response
                    # This will require some refactoring though. I could consider getting rid of the text generator type
                    has_finished_thinking = True
                has_finished_thinking = True
                yield from self._handle_part(parts[1])
    
    def _handle_part(self, part) -> Generator[str, None, None]:
        if "text" in part:
            yield part.text
            return

        if "executable_code" in part:
            language = part.executable_code.language.name.lower()
            if language == "language_unspecified":
                language = ""
            else:
                language = f" {language}"
            yield f"```{language}"
            yield part.executable_code.code.lstrip("\n")
            yield "```"
            return

        if "code_execution_result" in part:
            outcome_result = part.code_execution_result.outcome.name.lower().replace(
                "outcome_", ""
            )
            if outcome_result == "ok" or outcome_result == "unspecified":
                outcome_result = ""
            else:
                outcome_result = f" {outcome_result}"
            yield f"```{outcome_result}"
            yield part.code_execution_result.output
            yield "```"
            return

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
        return self.request_builder
