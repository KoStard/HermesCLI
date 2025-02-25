import time
from typing import Generator

from botocore.config import Config
from botocore.exceptions import ClientError
from hermes.interface.assistant.prompt_builder.simple_prompt_builder import SimplePromptBuilderFactory
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.bedrock import BedrockRequestBuilder
from .base import ChatModel

class BedrockModel(ChatModel):
    def initialize(self):
        self.request_builder = BedrockRequestBuilder(self.model_tag, self.notifications_printer, SimplePromptBuilderFactory())

        import boto3

        aws_region = self.config.get("aws_region")
        self.client = boto3.client('bedrock-runtime', region_name=aws_region, config=Config(connect_timeout=5, read_timeout=60, retries={'max_attempts': 5, 'mode': 'adaptive'}))
    
    def send_request(self, request: any) -> Generator[str, None, None]:
        response = self.client.converse_stream(
            **request
        )

        for event in response['stream']:
            if 'contentBlockDelta' in event:
                content = event['contentBlockDelta']['delta'].get('text', '')
                yield content
            elif 'messageStop' in event:
                break
    
    def get_request_builder(self) -> RequestBuilder:
        return self.request_builder

    @staticmethod
    def get_provider() -> str:
        return 'BEDROCK'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        return [
            'anthropic.claude-3-sonnet-20240229-v1:0',
            'anthropic.claude-3-5-sonnet-20240620-v1:0',
            'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'anthropic.claude-3-opus-20240229-v1:0',
            'mistral.mistral-large-2407-v1:0',
            'anthropic.claude-3-5-haiku-20241022-v1:0',
        ]
