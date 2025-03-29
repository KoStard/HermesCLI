from pathlib import Path
from typing import Dict, Generator, List

from hermes.interface.assistant.chat_assistant.response_types import (
    BaseLLMResponse,
    TextLLMResponse,
)
from hermes.interface.assistant.chat_models.base import ChatModel
from hermes.interface.assistant.deep_research_assistant.engine.llm_interface import (
    LLMInterface,
)
from hermes.interface.assistant.deep_research_assistant.engine.logger import (
    DeepResearchLogger,
)
from hermes.message import TextMessage
import logging

logger = logging.getLogger(__name__)


class ChatModelLLMInterface(LLMInterface):
    """Implementation of LLMInterface using ChatModel"""

    def __init__(self, model: ChatModel, research_dir: str = None):
        self.model = model
        self.research_dir = research_dir if research_dir else str(Path.cwd())
        self.deep_research_logger = DeepResearchLogger(Path(self.research_dir))

    def generate_request(
        self, static_help_interface: str, dynamic_interface: str, history_messages: List[dict], node_path: Path
    ) -> Dict:
        """Generate a request for the LLM based on the rendered interface and history"""
        request_builder = self.model.get_request_builder()

        logging_history = list(history_messages)

        # Convert history messages to TextMessage objects
        rendered_messages = [TextMessage(author="user", text=static_help_interface)]
        logging_history.insert(0, {
            "author": "user",
            "content": static_help_interface
        })

        # Add history messages
        for message in history_messages:
            rendered_messages.append(
                TextMessage(author=message["author"], text=message["content"])
            )

        if dynamic_interface:
            rendered_messages.append(TextMessage(author="user", text=dynamic_interface))
            logging_history.append({
                "author": "user",
                "content": dynamic_interface
            })

        # Build and return the request
        request = request_builder.build_request(rendered_messages)

        self.deep_research_logger.log_llm_request(node_path, logging_history, request)

        return request

    def send_request(self, request: Dict) -> Generator[str, None, None]:
        """Send a request to the LLM and get a generator of responses"""
        # Process the LLM response and handle thinking vs text tokens
        llm_responses_generator = self._handle_string_output(
            self.model.send_request(request)
        )

        # Collect the response
        llm_response = []
        is_thinking = False
        is_working = False
        for response in llm_responses_generator:
            if isinstance(response, TextLLMResponse):
                if is_thinking:
                    print("Thinking finished")
                    is_thinking = False
                if not is_working:
                    print("Working...", end="", flush=True)
                    is_working = True
                else:
                    print(".", end="", flush=True)
                llm_response.append(response.text)
                logger.debug(response.text)
            else:
                if not is_thinking:
                    is_thinking = True
                    print("Thinking...", end="", flush=True)
                else:
                    print(".", end="", flush=True)
                logger.debug(response.text)
        print()

        # Join the response parts and yield the final result
        full_llm_response = "".join(llm_response)
        yield full_llm_response

    def log_response(self, node_path, response: str) -> None:
        """Log an LLM response"""
        self.deep_research_logger.log_llm_response(node_path, response)

    def _handle_string_output(
        self, llm_response_generator: Generator[str, None, None]
    ) -> Generator[BaseLLMResponse, None, None]:
        """
        This is implemented for backwards compatibility, as not all models support thinking tokens yet and they currently just return string.
        """
        for response in llm_response_generator:
            if isinstance(response, str):
                yield TextLLMResponse(response)
            else:
                yield response
