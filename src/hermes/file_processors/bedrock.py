from .base import FileProcessor
from ..decorators import register_file_processor

@register_file_processor("bedrock")
class BedrockFileProcessor(FileProcessor):
    def read_file(self, file_path: str) -> bytes:
        # Currently unreliable: [Carry out a conversation - Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
        # Sonnet-3.5 in Bedrock doesn't support file chat.
        if not self.exists(file_path):
            return b"empty"

        with open(file_path, 'rb') as file:
            return file.read()
