import time
from typing import Generator

from botocore.config import Config
from botocore.exceptions import ClientError
from hermes.interface.assistant.chat_assistant.response_types import (
    TextLLMResponse,
    ThinkingLLMResponse,
)
from hermes.interface.assistant.prompt_builder.simple_prompt_builder import (
    SimplePromptBuilderFactory,
)
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.assistant.request_builder.bedrock import BedrockRequestBuilder
from .base import ChatModel


class BedrockModel(ChatModel):
    def initialize(self):
        self.request_builder = BedrockRequestBuilder(
            self.model_tag, self.notifications_printer, SimplePromptBuilderFactory()
        )

        import boto3

        aws_region = self.config.get("aws_region")
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=aws_region,
            config=Config(
                connect_timeout=5,
                read_timeout=3600,
                retries={"max_attempts": 5, "mode": "adaptive"},
            ),
        )
        self._low_reasoning_tokens = self.config.get("low_reasoning_tokens", 1024)
        self._medium_reasoning_tokens = self.config.get(
            "low_reasoning_tokens", 1024 * 5
        )
        self._high_reasoning_tokens = self.config.get("low_reasoning_tokens", 1024 * 10)

    def send_request(self, request: any) -> Generator[str, None, None]:
        response = self._call_and_retry_if_needed(request)

        for event in response["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                if "reasoningContent" in delta:
                    content = delta["reasoningContent"].get("text", "")
                    yield ThinkingLLMResponse(content)
                if "text" in delta:
                    content = delta.get("text", "")
                    yield TextLLMResponse(content)
            elif "messageStop" in event:
                break

    def _call_and_retry_if_needed(self, request, tries=1):
        try:
            response = self.client.converse_stream(**request)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if tries <= 3:
                    seconds = 10 * (tries ** 2)
                    print("Throttling Exception Occured.")
                    print("Retrying.....")
                    print("Attempt No.: " + str(tries))
                    print(f"Sleeping for {seconds}")
                    time.sleep(seconds)
                    return self._call_and_retry_if_needed(request, tries + 1)
                else:
                    print("Attempted 3 Times But No Success.")
                    print("Raising Exception.....")
                    raise
            else:
                raise
        return response


    def get_request_builder(self) -> RequestBuilder:
        return self.request_builder

    @staticmethod
    def get_provider() -> str:
        return "BEDROCK"

    @staticmethod
    def get_model_tags() -> list[str]:
        return [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-opus-20240229-v1:0",
            "mistral.mistral-large-2407-v1:0",
            "anthropic.claude-3-5-haiku-20241022-v1:0",
        ]

    def set_thinking_level(self, level: str):
        if hasattr(self.request_builder, "set_reasoning_effort"):
            if level == "low":
                level = self._low_reasoning_tokens
            elif level == "medium":
                level = self._medium_reasoning_tokens
            elif level == "high":
                level = self._high_reasoning_tokens
            else:
                raise ValueError(f"Invalid thinking level: {level}")
            self.request_builder.set_reasoning_effort(level)
