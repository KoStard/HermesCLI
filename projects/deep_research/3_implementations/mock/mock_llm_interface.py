from collections.abc import Generator

from hermes.chat.interface.assistant.agent.framework.llm_interface import (
    LLMInterface,
)


class MockLLMInterface(LLMInterface):
    """
    Mock implementation of LLMInterface that uses STDOUT/STDIN instead of calling an LLM.
    This allows a human to play the role of the LLM in the mock setup.
    """

    def __init__(self, research_dir: str):
        """Initialize the mock LLM interface"""
        self.research_dir = research_dir

    def generate_request(
        self,
        history_messages: list[dict],
        current_node_path,
    ) -> dict:
        """
        Generate a request for the LLM based on the rendered interface and history

        Args:

        Returns:
            Dict: The request object to send to the LLM
        """
        # For the mock, we just need to pass the rendered interface and history

        return {
            "interface": history_messages[0],
            "history": history_messages[1:],
        }

    def send_request(self, request: dict) -> Generator[str, None, None]:
        """
        Send a request to the LLM and get a generator of responses.
        In this mock implementation, it prints the interface to STDOUT
        and reads the response from STDIN.

        Args:
            request: The request object to send

        Returns:
            Generator[str, None, None]: Generator yielding LLM responses
        """
        # Clear the screen for better readability
        print("\033c", end="")  # ANSI escape code to clear screen

        # Print a clear separator
        print("\n" + "=" * 100)
        print("MOCK LLM INTERFACE - YOU ARE PLAYING THE ROLE OF THE AI ASSISTANT")
        print("=" * 100 + "\n")

        # Print the interface content
        print(request["interface"])

        # Print the chat history if available
        if request["history"]:
            print("\n" + "=" * 50)
            print("CHAT HISTORY:")
            print("=" * 50)
            for message in request["history"]:
                print(f"\n## {message['author']}")
                print(message["content"])
                print("-" * 50)

        print("\n" + "=" * 100)
        print("ENTER YOUR RESPONSE AS THE AI ASSISTANT (type END_RESPONSE on a new line when finished):")
        print("=" * 100 + "\n")

        # Collect the response from STDIN
        response_lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END_RESPONSE":
                    break
                response_lines.append(line)
            except EOFError:
                break

        full_response = "\n".join(response_lines)
        yield full_response
