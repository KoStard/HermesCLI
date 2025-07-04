import time
from collections.abc import Generator
from typing import Any

from hermes.chat.interface.assistant.chat.response_types import (
    TextLLMResponse,
    ThinkingLLMResponse,
)
from hermes.chat.interface.assistant.models.prompt_builder.simple_prompt_builder import (
    SimplePromptBuilderFactory,
)
from hermes.chat.interface.assistant.models.request_builder.base import RequestBuilder
from hermes.chat.interface.assistant.models.request_builder.bedrock import BedrockRequestBuilder

from .base import ChatModel


class BedrockModel(ChatModel):
    def initialize(self):
        import boto3
        from botocore.config import Config

        self.request_builder = BedrockRequestBuilder(self.model_tag, self.notifications_printer, SimplePromptBuilderFactory())

        aws_region = self.config.get("aws_region")
        aws_profile_name = self.config.get("aws_profile_name")

        if aws_profile_name:
            session = boto3.Session(profile_name=aws_profile_name)
            self.notifications_printer.print_notification(f"Using AWS profile: {aws_profile_name}")
        else:
            session = boto3.Session()  # Use default profile/credentials

        self.client = session.client(
            "bedrock-runtime",
            region_name=aws_region,
            config=Config(
                max_pool_connections=100,
                connect_timeout=5,
                read_timeout=3600,
                retries={"max_attempts": 5, "mode": "adaptive"},
            ),
        )

    def _process_content_delta(self, delta: dict) -> Generator[Any, None, None]:
        """Process the content delta from Bedrock response and yield appropriate responses."""
        if "reasoningContent" in delta:
            content = delta["reasoningContent"].get("text", "")
            yield ThinkingLLMResponse(content)
        if "text" in delta:
            content = delta.get("text", "")
            yield TextLLMResponse(content)

    def send_request(self, request: Any) -> Generator[str, None, None]:
        response = self._call_and_retry_if_needed(request)

        for event in response["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                yield from self._process_content_delta(delta)
            elif "messageStop" in event:
                break

    def _call_and_retry_if_needed(self, request, tries=1):
        from botocore.exceptions import ClientError

        try:
            response = self.client.converse_stream(**request)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ThrottlingException":
                if tries <= 5:
                    seconds = 20 * tries
                    print("Throttling Exception Occured.")
                    print("Retrying.....")
                    print("Attempt No.: " + str(tries))
                    print(f"Sleeping for {seconds}")
                    time.sleep(seconds)
                    return self._call_and_retry_if_needed(request, tries + 1)
                print("Attempted 3 Times But No Success.")
                print("Raising Exception.....")
                raise
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

    def set_thinking_level(self, level: int):
        self.request_builder.set_reasoning_effort(level)
