from typing import Generator
from .base import ChatModel
from ..registry import register_model
from google import auth
import google.auth.transport.requests as requests
import openai


@register_model(name="vertex", file_processor="default", prompt_builder="xml", config_key='VERTEX')
class VertexModel(ChatModel):
    def initialize(self):
        credentials, _ = auth.default()
        auth_request = requests.Request()
        credentials.refresh(auth_request)
        project_id = self.config.get("project_id")

        self.model_id = "meta/llama3-405b-instruct-maas"

        model_location = "us-central1"
        self.client = openai.OpenAI(
            base_url=f"https://{model_location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{model_location}/endpoints/openapi/chat/completions?",
            api_key=credentials.token,
        )

        super().initialize()

    def send_history(self, messages) -> Generator[str, None, None]:
        try:
            stream = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=True
            )
        except openai.AuthenticationError as e:
            raise Exception(
                "Authentication failed. Please check your API key.", e)
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
