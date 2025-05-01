from typing import List

from hermes.extensions_loader import load_extensions
from hermes.interface.assistant.deep_research_assistant.engine.engine import (
    DeepResearchEngine,
)
from .mock_llm_interface import MockLLMInterface


class DeepResearchMockApp:
    """Mock implementation of the Deep Research application for testing and development"""

    def __init__(
        self,
        instruction: str,
        initial_attachments: List[str] = None,
        root_dir: str = "research",
    ):
        # Load extensions
        _, _, _, deep_research_commands = load_extensions()

        # Create the mock LLM interface
        self.llm_interface = MockLLMInterface(root_dir)

        # Initialize the engine with the mock LLM interface and extensions
        self.engine = DeepResearchEngine(
            root_dir,
            self.llm_interface,
            # deep_research_commands,
        )

        self.engine.set_budget(2)

        self.instruction = instruction

    def start(self):
        """Start the mock application"""
        print("\nStarting Deep Research Mock Application...")
        print("You will play the role of the AI assistant.")
        print(
            "The system will show you the interface and you'll respond as if you were the AI."
        )
        print("Type 'END_RESPONSE' on a new line when you've finished your response.")

        # Print information about loaded extensions
        # if self.engine._extension_commands:
        #     print(
        #         f"\nLoaded {len(self.engine._extension_commands)} extension commands:"
        #     )
        #     for cmd_class in self.engine._extension_commands:
        #         print(f"- {cmd_class.__name__}")
        # else:
        #     print("\nNo extension commands loaded.")

        if not self.engine.is_root_problem_defined():
            success = self.engine.define_root_problem(self.instruction)
            if not success:
                raise ValueError("Failed to define root problem")

        # Execute the engine, which will use the mock LLM interface
        final_report = self.engine.execute()

        # Display the final report
        print("\n" + "=" * 80)
        print("DEEP RESEARCH COMPLETED")
        print("=" * 80)
        print(final_report)
