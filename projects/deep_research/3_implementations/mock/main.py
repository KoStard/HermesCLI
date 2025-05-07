#!/usr/bin/env python3
"""
Deep Research Mock Application

This is a mock implementation of the Deep Research system where:
1. The user's instructions are hardcoded
2. A human plays the role of the AI assistant through the terminal
3. No actual LLM calls are made

The mock uses STDOUT/STDIN to simulate the interaction between the system and the AI.
"""

import argparse
import os
from pathlib import Path

from .mock_app import DeepResearchMockApp


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Deep Research Mock Application")
    parser.add_argument(
        "--instruction",
        type=str,
        default="Please research and organize the fundamental concepts of quantum mechanics. I need a comprehensive understanding of the "
        "core principles that form the foundation of this field.",
        help="The research instruction",
    )
    parser.add_argument(
        "--research-dir",
        type=str,
        default=None,
        help="Directory to store research files (default: ./deep_research)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Configure logging if verbose mode is enabled
    if args.verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    # Use provided instruction or default
    instruction = args.instruction

    # Set up research directory
    research_dir = args.research_dir if args.research_dir else os.path.join(str(Path.cwd()), "deep_research")

    # Ensure the research directory exists
    os.makedirs(research_dir, exist_ok=True)

    # Example initial attachments (these would be mocked in a real scenario)
    initial_attachments = [
        "quantum_mechanics_intro.pdf",
        "https://en.wikipedia.org/wiki/Quantum_mechanics",
    ]

    # Initialize and start the mock app
    app = DeepResearchMockApp(instruction, initial_attachments, research_dir)

    try:
        app.start()
    except KeyboardInterrupt:
        print("\nExiting application...")
    except Exception:
        raise


if __name__ == "__main__":
    main()
