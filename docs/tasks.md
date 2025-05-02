## Task 1: Refactor Command Processing into a Reusable Subpackage

**Status:** Completed

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
- [x] 10. Help text generation/access mechanisms are part of the core package.
- [x] 11. Unit tests are created for the new core command package.
- [x] 12. Unit tests for the Deep Research command integration are updated.

**Components to Move (Examples):**
*   `command.py`: `Command`, `CommandSection`, `CommandRegistry`
*   `command_parser.py`: `CommandParser`, `CommandError`, `ParseResult`

**Components to Keep/Adapt (Examples):**
*   `command_context.py`: `CommandContext` (stays in Deep Research)
*   `commands.py`: Specific command implementations (stay in Deep Research, adapt inheritance)

**Rationale:**
Follows the "Don't Repeat Yourself" (DRY) principle and promotes code reuse. Allows for consistent command handling across different parts of the Hermes application. Improves separation of concerns, making the core command logic independent of specific execution environments.

## Task 2: Refactor Template Management into a Reusable Subpackage

**Status:** Completed

**Description:**
Extract the core template management logic from `hermes.interface.assistant.deep_research_assistant.engine.templates` into a new, reusable top-level subpackage, `hermes.interface.templates`. This aims to create a generic framework for template management that can be used across different interfaces within Hermes, similar to the command processing refactoring.

**Acceptance Criteria:**
- [X] 1. A new subpackage (`hermes.interface.templates`) is created.
- [X] 2. Core template management class (`TemplateManager`) is moved to the new subpackage.
- [X] 3. The moved components are generalized, removing dependencies specific to the Deep Research Assistant.
- [X] 4. The template loading and rendering logic resides within the new package.
- [X] 5. The Deep Research Assistant's template system is refactored to *use* the new `hermes.interface.templates` package.
- [X] 6. Template files (`.mako`) remain in Deep Research as they contain interface-specific content.
- [X] 7. Existing template functionality within Deep Research remains unchanged from a user/LLM perspective.
- [X] 8. Unit tests are created for the new core template package.

**Components to Move (Examples):**
*   `template_manager.py`: `TemplateManager`

**Components to Keep/Adapt (Examples):**
*   Template files (`.mako`) stay in Deep Research
*   Deep Research-specific template rendering and contexts

**Rationale:**
Follows the "Don't Repeat Yourself" (DRY) principle and promotes code reuse. Allows for consistent template management across different parts of the Hermes application. Improves separation of concerns, making the core template management logic independent of specific interfaces.

## Task 3: Migrate ChatAssistant to New Command Model

**Status:** Completed

**Description:**
Migrate the ChatAssistant interface to use the new Command model system created in Task 1. This involves replacing the old `///command...` syntax with the new generic command model (`<<< ... >>>`) while preserving all existing functionality.

**Acceptance Criteria:**
- [X] 1. Create command classes for all existing ChatAssistant commands that inherit from the base Command class
- [X] 2. Update the command parsing logic to use the new CommandParser
- [X] 3. Preserve all existing command functionality (file operations, markdown editing, utility commands, agent commands)
- [X] 4. Update the control panel to register and use these commands
- [X] 5. Update the message processing logic to properly handle the new command syntax
- [X] 6. Ensure proper command context for execution
- [X] 7. Comprehensive help text for all commands
- [X] 8. Support for examples using "#" prefix
- [X] 9. Maintain backward compatibility with existing code that uses ChatAssistantControlPanel

**Components Created/Modified:**
* `hermes/interface/assistant/chat_assistant/commands.py`: New file containing all command implementations
* `hermes/interface/assistant/chat_assistant/control_panel.py`: Updated to use the new command model
* `hermes/interface/commands/templates/command_help.mako`: Template for rendering command help

**Rationale:**
This migration standardizes command handling across the Hermes application, making it easier to maintain and extend. The new command model provides better error handling, validation, and help text generation. It also simplifies the addition of new commands in the future.

## Task 4: Simplify Command Processing by Moving Execution to Control Panel

**Status:** Completed

**Description:**
Simplify the command processing flow by moving execution logic from the engine to the control panel. Currently, the control panel parses commands and creates Events that are sent to the engine, which then performs the actual operations. We want to eliminate this indirection by having the control panel directly execute commands and provide feedback to the assistant, without going through the engine.

**Acceptance Criteria:**
- [ ] 1. Move execution logic from the engine to the control panel for all assistant commands. Keep the user control panel as is for now.
- [ ] 2. Implement a notification system specifically for the assistant that doesn't appear in the user interface. These should be saved in the history, so a new type of message.
- [ ] 3. Maintain all existing functionality and command capabilities
- [ ] 4. Ensure proper error handling at the control panel level
- [ ] 5. Maintain file path security and validation
- [ ] 6. Preserve file backup mechanisms
- [ ] 7. Commands that affect the engine state can continue using events.

**Risks and Considerations:**
1. **Separation of Concerns**: Moving execution to the control panel blurs the line between UI and business logic
2. **Error Handling**: Need robust error handling directly in the control panel
3. **File System Operations**: Need to replicate file backup mechanisms and security checks
4. **Engine State Synchronization**: Some commands affect the engine's state
5. **History Tracking**: Need to ensure bypassing the engine doesn't affect history recording
6. **Permission Checks**: Need to replicate any engine-level permission validations
7. **Testing Impact**: Changes may affect existing tests

**Questions for Clarification:**
1. Should we maintain any event emission for tracking/history purposes? yes
2. How should we handle commands that change system state (Done, AskTheUser)? still use events
3. Is there any existing notification system we can leverage for assistant-only notifications? yes, create a new class (or reuse) of messages that are visible only to the assistant
4. Are there engine-level permissions or validations that need to be maintained? no
5. Should we create a common utility library for file operations that both the engine and control panel can use? not yet

**Rationale:**
This change simplifies the architecture by removing an unnecessary layer of indirection. It should make the code more maintainable, easier to understand, and potentially more performant by eliminating the event passing overhead.
