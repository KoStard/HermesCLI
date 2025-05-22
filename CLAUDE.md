# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation & Setup
```bash
# Install dependencies using uv
uv pip install -e .
# Install dev dependencies
uv pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific tests
uv run pytest tests/path/to/test_file.py

# Run tests with coverage
uv run pytest --cov=hermes
```

### Code Quality
```bash
# Format code
uv run ruff format

# Run linters
uv run ruff check
uv run ruff check --fix
uv run ruff check --watch

# Type checking
uv run pyright
```

### Performance Testing
```bash
# Run import time performance test
uv run invoke performance-test-with-import
```

## Core Architecture

Hermes is an extendable CLI interface for interacting with Large Language Models (LLMs). The project is structured as follows:

### Key Components

1. **Chat Engine** (`hermes/chat/engine.py`): Central component that orchestrates messages between user and LLM.

2. **Interface System** (`hermes/chat/interface/`):
   - User interface for command handling
   - Assistant interfaces for different model implementations
   - Command parsing and execution

3. **Model Support** (`hermes/chat/interface/assistant/models/`):
   - Support for multiple LLM providers through adapter pattern
   - Model factory for creating appropriate model instances

4. **Command System**:
   - User commands (prefixed with `/`)
   - LLM commands (structured as blocks with `<<< command_name` and `>>>` delimiters)
   - Command sections defined with `///section_name` within command blocks
   - Command validation and execution framework
   - Extensible through extensions

5. **Deep Research Agent** (`hermes/chat/interface/assistant/agent/deep_research/`):
   - Advanced research capabilities
   - Problem definition and hierarchy management
   - Artifact management and reporting

### Extension System

Custom functionality can be added through extensions in `~/.config/hermes/extensions/`. Each extension should have its own subdirectory with an `extension.py` file that may implement:

- User commands via `get_user_extra_commands()`
- LLM commands via `get_llm_extra_commands()`
- Utility commands via `get_utils_builders()`

### Command Implementation

LLM commands in Hermes follow a specific structure:

1. **Command Definition**:
   - Commands are defined by extending the `Command` class
   - Each command has a name and optional help text
   - Commands define their required and optional sections

2. **Command Structure**:
   ```
   <<< command_name
   ///section1
   Content for section1
   ///section2
   Content for section2
   >>>
   ```

3. **Command Processing**:
   - The `CommandParser` identifies command blocks and sections
   - Commands are validated for required sections and section content
   - Command arguments can be transformed before execution
   - Each command implements an `execute` method that receives parsed sections

## Development Guidelines

1. Use UV commands instead of directly using python or pip
2. Follow Clean Code principles with clean and intuitive naming
3. Maintain test coverage for new functionality
4. Preserve existing architectural patterns when adding new features
