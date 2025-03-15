import os
from typing import List

from hermes.interface.assistant.deep_research_assistant.engine.engine import DeepResearchEngine


class DeepResearchMockApp:
    """Mock implementation of the Deep Research application for testing and development"""
    
    def __init__(
        self,
        instruction: str,
        initial_attachments: List[str] = None,
        root_dir: str = "research",
    ):
        self.engine = DeepResearchEngine(instruction, initial_attachments, root_dir)
    
    def start(self):
        """Start the mock application"""
        self._render_interface()

        while not self.engine.finished:
            try:
                user_input = self._get_multiline_input()
                self._process_input(user_input)
            except KeyboardInterrupt:
                print("\nExiting application...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _render_interface(self):
        """Render the interface to the console"""
        os.system("cls" if os.name == "nt" else "clear")

        # First render the interface
        interface_content = self.engine.get_interface_content()
        print(interface_content)

        # Always render the chat history regardless of problem definition status
        if self.engine.chat_history.messages:
            print("\n" + "=" * 70)
            print("# CHAT HISTORY")
            print("=" * 70)
            print(self.get_formatted_history(self.engine.chat_history))
            
    def get_formatted_history(self, history) -> str:
        """Get the formatted history as a string"""
        if not history.messages:
            return "No previous messages in this focus level."

        result = []
        for message in history.messages:
            result.append(f"## {message.author}")
            result.append(message.content)
            result.append("\n" + "-" * 50 + "\n")  # Separator between messages

        return "\n".join(result)

    
    def _get_multiline_input(self) -> str:
        """Get multiline input from the user"""
        lines = []

        while True:
            try:
                line = input()
                if line == "\x1b":  # Escape character
                    break
                lines.append(line)
            except EOFError:
                break

        return "\n".join(lines)
    
    def _process_input(self, text: str):
        """Process user input"""
        # Process commands using the engine
        self.engine.process_commands(text)
        
        # Re-render the interface after processing commands
        self._render_interface()
