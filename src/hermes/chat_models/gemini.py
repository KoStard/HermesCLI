from typing import Generator
from .base import ChatModel
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiModel(ChatModel):
    def initialize(self):
        api_key = self.config["GEMINI"]["api_key"]
        genai.configure(api_key=api_key)
        self.chat = genai.GenerativeModel('gemini-1.5-pro-exp-0801').start_chat(history=[])

    def send_message(self, message: str) -> Generator[str, None, None]:
        response = self.chat.send_message(message, stream=True, safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        })
        for chunk in response:
            yield chunk.text
