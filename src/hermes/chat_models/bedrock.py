import configparser
from typing import Generator
from .base import ChatModel
import boto3
from ..decorators import register_model

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
        self.messages = []

    def send_message(self, message) -> Generator[str, None, None]:
        if isinstance(message, str):
            message = [{'text': message}]
        # Sorting to put the texts in the end, fails with strange error otherwise
        message.sort(key=lambda x: 'text' in x)
        temp_messages = self.messages.copy()
        temp_messages.append(self.create_message('user', message))
        response = self.client.converse_stream(
            modelId=self.model_id,
            messages=temp_messages
        )

        full_response = ""
        for event in response['stream']:
            if 'contentBlockDelta' in event:
                content = event['contentBlockDelta']['delta'].get('text', '')
                full_response += content
                yield content
            elif 'messageStop' in event:
                break

        self.messages.append(self.create_message('user', message))
        self.messages.append(self.create_message('assistant', [{'text': full_response}]))

    def create_message(self, role, content):
        return {
            'role': role,
            'content': content
        }
    
    def send_history(self, messages) -> Generator[str, None, None]:
        response = self.client.converse_stream(
            modelId=self.model_id,
            messages=messages
        )

        full_response = ""
        for event in response['stream']:
            if 'contentBlockDelta' in event:
                content = event['contentBlockDelta']['delta'].get('text', '')
                full_response += content
                yield content
            elif 'messageStop' in event:
                break
