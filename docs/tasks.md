## Task 1: Refactor Command Processing into a Reusable Subpackage

**Status:** In Progress

**Description:**
Extract the core command processing logic from `hermes.interface.assistant.deep_research_assistant.engine.commands` into a new, reusable top-level subpackage, `hermes.interface.commands`. This aims to create a generic framework for defining, registering, parsing, and validating commands that can be used across different interfaces within Hermes (e.g., Deep Research Assistant, also replacing the current Chat Assistant command processing).

**Acceptance Criteria:**
- [X] 1. A new subpackage (`hermes.interface.commands`) is created.
- [X] 2. Core classes/concepts (`Command`, `CommandSection`, `CommandRegistry`, `CommandParser`, `CommandError`, `ParseResult`) are moved to the new subpackage.
- [X] 3. The moved components are generalized, removing dependencies specific to the Deep Research Assistant's engine or context.
- [X] 4. The command parsing logic (block and section syntax) resides within the new package.
- [X] 5. The `Command` base class defines an abstract `execute` method generic over the execution context, passed in by the calling interface.
- [X] 6. The Deep Research Assistant's command system (`hermes.interface.assistant.deep_research_assistant.engine.commands`) is refactored to *use* the new `hermes.interface.commands` package.
- [X] 7. Specific command implementations (e.g., `AddCriteriaCommand`) remain in Deep Research but inherit from the new core `Command` class.
- [X] 8. `CommandContext` remains within Deep Research and is passed to the `execute` method.
- [x] 9. Existing command functionality within Deep Research remains unchanged from a user/LLM perspective (Needs testing).
- [ ] 10. Help text generation/access mechanisms are part of the core package.
- [ ] 11. Unit tests are created for the new core command package.
- [x] 12. Unit tests for the Deep Research command integration are updated.

**Components to Move (Examples):**
*   `command.py`: `Command`, `CommandSection`, `CommandRegistry`
*   `command_parser.py`: `CommandParser`, `CommandError`, `ParseResult`

**Components to Keep/Adapt (Examples):**
*   `command_context.py`: `CommandContext` (stays in Deep Research)
*   `commands.py`: Specific command implementations (stay in Deep Research, adapt inheritance)

**Rationale:**
Follows the "Don't Repeat Yourself" (DRY) principle and promotes code reuse. Allows for consistent command handling across different parts of the Hermes application. Improves separation of concerns, making the core command logic independent of specific execution environments.
