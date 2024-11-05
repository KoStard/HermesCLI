from typing import Generator
from ..registry import register_model
from .base import ChatModel

@register_model(name=["bedrock/sonnet-3", "bedrock/sonnet-3.5","bedrock/sonnet-3.5-v2", "bedrock/opus-3", "bedrock/mistral", "bedrock/haiku-3.5-v2"], file_processor="default", prompt_builder="bedrock", config_key='BEDROCK')
class BedrockModel(ChatModel):
    def initialize(self):
        import boto3

        aws_region = self.config.get("aws_region")
        self.client = boto3.client('bedrock-runtime', region_name=aws_region)
        model_identifier = self.config["model_identifier"]
        self.model_id = self.get_model_id(model_identifier)
    
    def get_model_id(self, model_identifier):
        if model_identifier == 'bedrock/sonnet-3':
            return 'anthropic.claude-3-sonnet-20240229-v1:0'
        elif model_identifier == 'bedrock/sonnet-3.5':
            return 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        elif model_identifier == 'bedrock/sonnet-3.5-v2':
            return 'anthropic.claude-3-5-sonnet-20241022-v2:0'
        elif model_identifier == 'bedrock/opus-3':
            return 'anthropic.claude-3-opus-20240229-v1:0'
        elif model_identifier == 'bedrock/mistral':
            return 'mistral.mistral-large-2407-v1:0'
        elif model_identifier == 'bedrock/haiku-3.5-v2':
            return 'anthropic.claude-3-5-haiku-20241022-v1:0'
        else:
            raise ValueError(f"Unsupported Bedrock model identifier: {model_identifier}")

    def send_history(self, messages) -> Generator[str, None, None]:
        system_message = []
        if messages[0]['role'] == 'system':
            system_message = messages[0]['content']
            messages = messages[1:]
        response = self.client.converse_stream(
            modelId=self.model_id,
            messages=messages,
            system=system_message
        )

        for event in response['stream']:
            if 'contentBlockDelta' in event:
                content = event['contentBlockDelta']['delta'].get('text', '')
                yield content
            elif 'messageStop' in event:
                break
