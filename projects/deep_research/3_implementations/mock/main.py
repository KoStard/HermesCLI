#!/usr/bin/env python3
# This is the entry point of the program
# Don't write everything in one file
# Create multiple files, create classes, proper abstractions making the interface simple, yet directly implementing the requirements
# Use best practices for the code, keep it well maintainable and flexible in the prompt structures, parsers, etc.
# Implementation starts below this comment
# Even though currently we are making a mock, we are mocking only a few pieces, the code should be real and up to the standards for the rest.
# We are mocking: 
# 1. There is no user, the user input (the instructions) we'll hardcode in the __name__ == __main__ section for now.
# 2. We don't make actual calls to the LLM, instead we print to the terminal allowing a person to reply to it, playing the role of the LLM
# ------

import os
from pathlib import Path
from .app import DeepResearchApp


def main():
    # Hardcoded instruction for now
    instruction = "Please research and organize the fundamental concepts of quantum mechanics. I need a comprehensive understanding of the core principles that form the foundation of this field."
    
    # Hardcoded initial attachments for now
    initial_attachments = [
        "quantum_mechanics_intro.pdf",
        "https://en.wikipedia.org/wiki/Quantum_mechanics"
    ]
    
    # Create a research directory in the user's home directory
    research_dir = os.path.join(str(Path.cwd()), "deep_research")
    
    # Initialize the FileSystem with the research directory
    app = DeepResearchApp(instruction, initial_attachments, research_dir)
    
    print(f"Starting Deep Research. Files will be saved to: {research_dir}")
    app.start()


if __name__ == "__main__":
    main()
