from typing import Generator
import boto3
from ..decorators import register_model
from .base import ChatModel

@register_model(name=["bedrock/sonnet-3", "bedrock/sonnet-3.5", "bedrock/opus-3", "bedrock/mistral"], file_processor="default", prompt_builder="bedrock", config_key='BEDROCK')
class BedrockModel(ChatModel):
    def initialize(self):
        self.client = boto3.client('bedrock-runtime')
        self.model_id = self.config.get("model_id", "anthropic.claude-3-sonnet-20240229-v1:0")

    def send_history(self, messages) -> Generator[str, None, None]:
        response = self.client.converse_stream(
            modelId=self.model_id,
            messages=messages
        )

        for event in response['stream']:
            if 'contentBlockDelta' in event:
                content = event['contentBlockDelta']['delta'].get('text', '')
                yield content
            elif 'messageStop' in event:
                break
