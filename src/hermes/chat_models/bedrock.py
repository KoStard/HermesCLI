from typing import Generator
import boto3
from ..decorators import register_model
from .base import ChatModel

@register_model(["bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral"], "default", "bedrock")
class BedrockModel(ChatModel):
    def initialize(self):
        self.client = boto3.client('bedrock-runtime')
        if self.model_tag == 'bedrock-claude':
            self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        elif self.model_tag == 'bedrock-claude-3.5':
            self.model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        elif self.model_tag == 'bedrock-opus':
            self.model_id = 'anthropic.claude-3-opus-20240229-v1:0'
        else:
            self.model_id = 'mistral.mistral-large-2407-v1:0'

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
