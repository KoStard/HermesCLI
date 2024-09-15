from typing import Generator
import boto3
from ..decorators import register_model
from .base import ChatModel

@register_model(name=["bedrock/sonnet-3", "bedrock/sonnet-3.5", "bedrock/opus-3", "bedrock/mistral"], file_processor="default", prompt_builder="bedrock", config_key='BEDROCK')
class BedrockModel(ChatModel):
    def initialize(self):
        self.client = boto3.client('bedrock-runtime')
        model_identifier = self.config["model_identifier"]
        self.model_id = self.get_model_id(model_identifier)
    
    def get_model_id(self, model_identifier):
        if model_identifier == 'bedrock-claude':
            return 'anthropic.claude-3-sonnet-20240229-v1:0'
        elif model_identifier == 'bedrock-claude-3.5':
            return 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        elif model_identifier == 'bedrock-opus':
            return 'anthropic.claude-3-opus-20240229-v1:0'
        elif model_identifier == 'bedrock-mistral':
            return 'mistral.mistral-large-2407-v1:0'

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
