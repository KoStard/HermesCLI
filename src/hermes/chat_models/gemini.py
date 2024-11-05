from typing import Generator
from .base import ChatModel
from ..registry import register_model


@register_model(name=[
    "gemini",
    "gemini/1.5-pro-exp-0801",
    "gemini/1.5-pro-exp-0827",
    "gemini/1.5-pro-002"
], file_processor="default", prompt_builder="xml", config_key='GEMINI')
class GeminiModel(ChatModel):
    def initialize(self):
        import google.generativeai as genai

        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Gemini model")
        model_identifier = self.config["model_identifier"]
        self.model_name = self.get_model_id(model_identifier)
        genai.configure(api_key=api_key)

    def send_history(self, messages) -> Generator[str, None, None]:
        from google.generativeai.types import ContentDict, HarmCategory, HarmBlockThreshold
        import google.generativeai as genai
        
        system_message = ""
        if messages[0]['role'] == 'system':
            system_message = '\n'.join([m.get('text') for m in messages[0]['content'] if m.get('text')])
            messages = messages[1:]
        
        extra_args = {}
        if system_message:
            extra_args['system_instruction'] = system_message

        self.model = genai.GenerativeModel(self.model_name, **extra_args)

        history = [ContentDict(
            role=self._get_message_role(msg['role']), parts=[msg['content']]) for msg in messages[:-1]]
        chat = self.model.start_chat(history=history)
        response = chat.send_message(messages[-1]['content'], stream=True, safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        })
        for chunk in response:
            yield chunk.text

    def _get_message_role(self, role):
        if role == 'user':
            return "user"
        return "model"

    def get_model_id(self, model_identifier):
        if model_identifier == 'gemini/1.5-pro-exp-0801':
            return 'gemini-1.5-pro-exp-0801'
        elif model_identifier == 'gemini/1.5-pro-exp-0827':
            return 'gemini-1.5-pro-exp-0827'
        elif model_identifier == 'gemini/1.5-pro-002':
            return 'gemini-1.5-pro-002'
        elif model_identifier == 'gemini':
            return self.config.get("model", "gemini-1.5-pro-exp-0827")
