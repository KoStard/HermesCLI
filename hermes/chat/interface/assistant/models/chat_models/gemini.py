from collections.abc import Generator

from hermes.chat.interface.assistant.chat_assistant.response_types import (
    BaseLLMResponse,
    TextLLMResponse,
    ThinkingLLMResponse,
)
from hermes.chat.interface.assistant.models.prompt_builder.simple_prompt_builder import (
    SimplePromptBuilderFactory,
)
from hermes.chat.interface.assistant.models.request_builder.base import RequestBuilder
from hermes.chat.interface.assistant.models.request_builder.gemini import GeminiRequestBuilder

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
        return "thinking" in self.model_tag

    def send_request(self, request: any) -> Generator[str, None, None]:
        import google.generativeai as genai

        model = genai.GenerativeModel(**request["model_kwargs"])

        chat = model.start_chat(history=request["history"])
        response = chat.send_message(**request["message"])
        has_finished_thinking = not self._supports_thinking
        for chunk in response:
            parts = chunk.candidates[0].content.parts
            if not parts:
                continue
            yield from self._convert_to_llm_response(self._handle_part(parts[0]), is_thinking=not has_finished_thinking)

            if len(response._result.candidates[0].content.parts) == 2 or len(parts) == 2:
                # Sometimes the len(parts) is 1, but the next chunk is already of the response.
                has_finished_thinking = True

            if len(parts) == 2:
                yield from self._convert_to_llm_response(self._handle_part(parts[1]), is_thinking=not has_finished_thinking)

    def _handle_part(self, part) -> Generator[str, None, None]:
        if "text" in part:
            yield part.text
            return

        if "executable_code" in part:
            language = part.executable_code.language.name.lower()
            language = "" if language == "language_unspecified" else f" {language}"
            yield f"```{language}"
            yield part.executable_code.code.lstrip("\n")
            yield "```"
            return

        if "code_execution_result" in part:
            outcome_result = part.code_execution_result.outcome.name.lower().replace("outcome_", "")
            outcome_result = "" if outcome_result == "ok" or outcome_result == "unspecified" else f" {outcome_result}"
            yield f"```{outcome_result}"
            yield part.code_execution_result.output
            yield "```"
            return

    def _convert_to_llm_response(self, responses: Generator[str, None, None], is_thinking: bool) -> Generator[BaseLLMResponse, None, None]:
        for response in responses:
            # response += "\n"
            if is_thinking:
                yield ThinkingLLMResponse(response)
            else:
                yield TextLLMResponse(response)

    @staticmethod
    def get_provider() -> str:
        return "GEMINI"

    @staticmethod
    def get_model_tags() -> list[str]:
        models = [
            "gemini-1.5-pro-exp-0801",
            "gemini-1.5-pro-exp-0827",
            "gemini-exp-1206",
            "gemini-1.5-pro-002",
            "gemini-1.5-flash-002",
            "gemini-exp-1114",
            "gemini-1.5-pro-002/grounded",
        ]
        return models

    def get_request_builder(self) -> RequestBuilder:
        return self.request_builder
