from pathlib import Path

from hermes.chat.interface.assistant.framework import AgentEngine
from hermes.extensions_loader import load_extensions

from .mock_llm_interface import MockLLMInterface


class DeepResearchMockApp:
    """Mock implementation of the Deep Research application for testing and development"""

    def __init__(
        self,
        instruction: str,
        initial_attachments: list[str] = None,
        root_dir: str = "research",
    ):
        # Load extensions
        _, _, _, deep_research_commands = load_extensions()

        # Create the mock LLM interface
        self.llm_interface = MockLLMInterface(root_dir)

        # Initialize the engine with the mock LLM interface and extensions
        self.engine = AgentEngine(
            Path(root_dir),
            self.llm_interface,
            # deep_research_commands,
        )

        self.engine.set_budget(2)

        self.instruction = instruction

    def start(self):
        """Start the mock application"""
        print("\nStarting Deep Research Mock Application...")
        print("You will play the role of the AI assistant.")
        print("The system will show you the interface and you'll respond as if you were the AI.")
        print("Type 'END_RESPONSE' on a new line when you've finished your response.")

        if not self.engine.is_research_initiated():
            self.engine.define_root_problem(self.instruction)
        else:
            self.engine.add_new_instruction(self.instruction)

        # Execute the engine, which will use the mock LLM interface
        final_report = self.engine.execute()

        # Display the final report
        print("\n" + "=" * 80)
        print("DEEP RESEARCH COMPLETED")
        print("=" * 80)
        print(final_report)
