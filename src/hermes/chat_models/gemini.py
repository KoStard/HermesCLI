from typing import Generator
from .base import ChatModel
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from ..decorators import register_model

@register_model("gemini", "default", "xml")
class GeminiModel(ChatModel):
    def initialize(self):
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Gemini model")
        genai.configure(api_key=api_key)
        model_name = self.config.get("model", "gemini-1.5-pro-exp-0801")
        self.model = genai.GenerativeModel(model_name)

    def send_history(self, messages) -> Generator[str, None, None]:
        history = [genai.types.ContentDict(role=msg['role'], parts=[msg['content']]) for msg in messages[:-1]]
        chat = self.model.start_chat(history=history)
        response = chat.send_message(messages[-1]['content'], stream=True, safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        })
        for chunk in response:
            yield chunk.text
