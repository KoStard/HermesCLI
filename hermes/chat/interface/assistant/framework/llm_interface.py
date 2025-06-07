from abc import ABC, abstractmethod
from collections.abc import Generator
from pathlib import Path


class LLMInterface(ABC):
    """
    Abstract interface for LLM interaction
    Kept as abstract interface, as we also have a mock implementation for testing.
    """

    @abstractmethod
    def generate_request(
        self,
        history_messages: list[dict],
        node_path: Path,
    ) -> dict:
        """
        Generate a request for the LLM based on the rendered interface and history

        Args:
            history_messages: List of message dictionaries with author and content
            node_path: For logging

        Returns:
            Dict: The request object to send to the LLM
        """
        pass

    @abstractmethod
    def send_request(self, request: dict) -> Generator[str, None, None]:
        """
        Send a request to the LLM and get a generator of responses

        Args:
            request: The request object to send

        Returns:
            Generator[str, None, None]: Generator yielding LLM responses
        """
        pass
