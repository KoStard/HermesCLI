from collections.abc import Generator

from hermes.chat.interface.assistant.framework.llm_interface import (
    LLMInterface,
)


class MockLLMInterface(LLMInterface):
    """Mock implementation of LLMInterface that uses STDOUT/STDIN instead of calling an LLM.
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
        """Generate a request for the LLM based on the rendered interface and history

        Args:

        Returns:
            Dict: The request object to send to the LLM
        """
        # For the mock, we just need to pass the rendered interface and history

        return {
            "interface": history_messages[0],
            "history": history_messages[1:],
        }

    def _clear_screen_and_print_header(self):
        """Clear the screen and print the header for the mock interface."""
        print("\033c", end="")  # ANSI escape code to clear screen
        print("\n" + "=" * 100)
        print("MOCK LLM INTERFACE - YOU ARE PLAYING THE ROLE OF THE AI ASSISTANT")
        print("=" * 100 + "\n")

    def _print_interface_content(self, interface_content):
        """Print the interface content."""
        print(interface_content)

    def _print_chat_history(self, history):
        """Print the chat history if available."""
        if not history:
            return

        print("\n" + "=" * 50)
        print("CHAT HISTORY:")
        print("=" * 50)
        for message in history:
            print(f"\n## {message['author']}")
            print(message["content"])
            print("-" * 50)

    def _print_input_prompt(self):
        """Print the prompt for user input."""
        print("\n" + "=" * 100)
        print("ENTER YOUR RESPONSE AS THE AI ASSISTANT (type END_RESPONSE on a new line when finished):")
        print("=" * 100 + "\n")

    def _collect_response_from_stdin(self) -> str:
        """Collect response from standard input until END_RESPONSE is entered."""
        response_lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END_RESPONSE":
                    break
                response_lines.append(line)
            except EOFError:
                break

        return "\n".join(response_lines)

    def send_request(self, request: dict) -> Generator[str, None, None]:
        """Send a request to the LLM and get a generator of responses.
        In this mock implementation, it prints the interface to STDOUT
        and reads the response from STDIN.

        Args:
            request: The request object to send

        Returns:
            Generator[str, None, None]: Generator yielding LLM responses
        """
        self._clear_screen_and_print_header()
        self._print_interface_content(request["interface"])
        self._print_chat_history(request["history"])
        self._print_input_prompt()

        full_response = self._collect_response_from_stdin()
        yield full_response
