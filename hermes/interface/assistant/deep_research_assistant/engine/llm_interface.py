from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Generator, List



class LLMInterface(ABC):
    """Abstract interface for LLM interaction"""

    @abstractmethod
    def generate_request(
        self, static_help_interface: str, dynamic_interface: str, history_messages: List[dict], node_path: Path
    ) -> Dict:
        """
        Generate a request for the LLM based on the rendered interface and history

        Args:
            static_help_interface: The rendered static interface content as a string
            dynamic_interface: The rendered dynamic interface content as a string
            history_messages: List of message dictionaries with author and content
            node_path: For logging

        Returns:
            Dict: The request object to send to the LLM
        """
        pass

    @abstractmethod
    def send_request(self, request: Dict) -> Generator[str, None, None]:
        """
        Send a request to the LLM and get a generator of responses

        Args:
            request: The request object to send

        Returns:
            Generator[str, None, None]: Generator yielding LLM responses
        """
        pass

    @abstractmethod
    def log_response(self, node_path, response: str) -> None:
        """
        Log an LLM response

        Args:
            node_path: Path to the current node
            response: The response from the LLM
        """
        pass
