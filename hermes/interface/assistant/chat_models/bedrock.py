import time
from typing import Generator

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
        self.client = boto3.client('bedrock-runtime', region_name=aws_region)
    
    def send_request(self, request: any) -> Generator[str, None, None]:
        backoff = 4
        max_retries = 5
        attempt = 0

        while attempt < max_retries:
            try:
                response = self.client.converse_stream(
                    **request
                )

                for event in response['stream']:
                    if 'contentBlockDelta' in event:
                        content = event['contentBlockDelta']['delta'].get('text', '')
                        yield content
                    elif 'messageStop' in event:
                        break
                return  # Success - exit the retry loop
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException':
                    if attempt == max_retries - 1:
                        raise  # Re-raise on last attempt
                    
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                    attempt += 1
                else:
                    raise  # Re-raise if it's not a ThrottlingException
    
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
