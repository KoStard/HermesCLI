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
   - Never use python directly in your commands, always use it through UV. like uv run python
2. Follow Clean Code principles with clean and intuitive naming
3. Maintain test coverage for new functionality
4. Preserve existing architectural patterns when adding new features

## Development Philosophy

### Generic
- This codebase follows Daoism. The code should flow like water, non-doing, not forced, natural code.
- The code follows Uncle Bob's definition of Clean Code. Follow all the best practices, in exceptional cases, when breaking them, ask for confirmation.
- The code should remain flexible. Don't repeat, don't create many tests for the same capability, keep things lean, to easily adjust and change
- Development is partitioned by subpackage. Don't spread development throughout multiple subpackages. Start development on one module, finish, run the tests, then move to the next. Don't parallelize.
- Always write production code. Code that you can happily publish online or let a teammate to review. Don't leave unnecessary comments.
- Always leave the codebase in better shape than before you touched it. If you see small syntax issues, go ahead and solve. If you see bigger problems, create tasks in backlog.
- Never try to solve vague problem directly. Instead, ask for clarifications or more information, write a high level plan and review, then break down into subproblems, create a tracker document with a checklist, and step by step solve while maintaining the tracker document.
- Use """ for multiline strings
- Avoid hacks and workarounds at all costs. Remember, single purpose components, as written in Clean Code. The thing you want to use, was it built for this? If the answer is not a sound yes, go into deeper design.
- We are still in development, don't aim to keep everything backwards compatible
- For internal-only changes, don't worry about backwards compatibility between modules, go ahead and change everything that needs to be changed to use the new interfaces
- Programming is closest to painting. So remember to think about your work also from aesthetic point of view, it should be clean and beautiful.
- Write beautiful and clean code. If you see something that's not clean, improve it, but don't change behaviour. Remember, it's not only about moving a line of code to another place, but it's about designing nicely the codepaths and flow itself. The code should be flowing well, and if it isn't, we should fix it.

### Project Management
- Employ iterative development: Plan phases, deliver incrementally, and adapt based on feedback or changing requirements.
- Define clear scope: Establish boundaries early (e.g., Charter & Scope in a project plan) and manage scope creep proactively.
- Practice risk management: Identify potential risks, assess their impact, and define mitigation strategies upfront (e.g., Risks & Mitigation in a project plan).
- Maintain project visibility: Use planning documents and task trackers (`tasks.md`) to ensure alignment and track progress.

### Task Management
- Follow Kanban principles: Address tasks from `tasks.md` sequentially, one at a time. Focus on completing a task before starting the next.
- When the user asks to create a task, add it to the tasks.md file.
- Update task status in `tasks.md` upon completion or if blocked.
- Ensure code changes directly address the acceptance criteria of the current task.
- For complex tasks requiring planning or design, create draft documents (e.g., markdown files) within `docs/tasks/{task_id}/` for review or clarification before implementation.
- It's your responsibility to update the task statuses.
- Work only on one task at a time.
- For requests without existing tasks, always create a task and track it there.

### Design Documents
- By "design document" we refer to a document that clearly calls out the problem we are trying to solve, defines the terms, list assumptions, provides historic/tech context, then from first principles builds up the possible solutions using different approaches/perspectives/models/philosophies. Then provides a recommended path forward.
- Then we go through reviews of the document, you accept feedback, provide more information if needed, adjust the document as needed, while trying to foresee possible issues and risks.
- We write design documents for non-trivial tasks.

### Coding
- Use Clean Code principles. Approach to this like craftsmanship.
- Minimize unnecessary comments. If there is need for comments, there is likely need to simplify. Either do it or create a task for that.
- Functions do single things. Functions are verbs.
- Classes are single things. Classes are nouns.

### Testing
- Create unit tests for each package, verifying the public methods
- Use clear naming pattern for the test names: `test_methodName_expectedBehaviour_inWhichSituation` - even if the method_name uses snake case, convert it to camelCase like methodName
- Test-driven development - write the unit test for the capability you want, then implement
- Remember, code needs to be written testable, not all code is testable.
- For testing using pytest, use fixtures if needed
- In the tests write dummy data, never put real paths/names/data
- When checking strings, verify the whole string at once, don't just check pieces. Use multiline text blocks if needed. So write only one assert if you anyway want to verify the whole string.
- Use AAA (Arrange, Act, Assert)
- Create a class per test file, add the unit tests inside the class
- Prefer automated tests over manual tests
- Test files should mimic the source code directory structure. A/B/C.py will be tested in tests/A/B/test_C.py
- Write minimum number of tests, while making sure all features/capabilities are covered. Use black box testing approach, testing the contract through the public methods. Test internals only in rare cases when it's an important logic hard to test from outside.

### Implementation
- Create subpackages in python
- Create interface (ABC) in __init__.py, don't import the implementation here
- Use dependency injection from the `main` function when instantiating the implementations
- Have separate files for the implementation classes
- Nest packages logically
- Check if the interface needs to be updated, does it pass all the necessary information?
- Have detailed logging (through `logger = logging.getLogger(__name__)`) with debug, concise with info
- In case you are lacking information about another class in a different subpackage, that means the interface is not good enough defined. Update the interface, maybe add return type, documentation, then ask the user to work with the team to make sure the implementation matches that interface. You can't have access to the implementation from a different subpackage.
- You find the simplest solutions for even difficult and complex problems. This might include updating existing pieces, removing some, or adding new ones.
- Whenever adding TODOs, always include a reference to a task where the TODO will be cleaned up/resolved.
- Write lean code, don't create backup solutions/codepaths if not necessary. Find the right way and see if that can be the only way, support complexity only if needed.

## Core Philosophy
- Don't focus on backwards compatibility. We are in active development, we shouldn't aim to support every previous decision we have made. Focus on great product and great code quality.

## Memories
- Instead of hasattr check the type of the object.
- Verify the prod readiness of your changes by running uv run ruff check. Also run uv run ruff format to format the code.