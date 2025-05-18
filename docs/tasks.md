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

## Task 5: Refactor Command Processing and Focus Logic

**Status:** Completed

**Description:**
Refactor the command processing flow and focus change logic.
The `CommandContext` should have a reference to the `CommandProcessor` that created it.
The `AgentEngine`'s focus change methods (`focus_down`, `focus_up`, `fail_and_focus_up`) should be moved to the `CommandProcessor`.

**Acceptance Criteria:**
- [X] 1. `CommandContextFactory` and its implementations are updated to pass the `CommandProcessor` instance to the `CommandContext` constructor.
- [X] 2. `CommandContext` (specifically `CommandContextImpl`) stores and uses this `CommandProcessor` reference.
- [X] 3. The `focus_down`, `focus_up`, and `fail_and_focus_up` methods are moved from `AgentEngine` to `CommandProcessor`.
- [X] 4. `CommandContextImpl` updates its focus methods to call the methods on its `CommandProcessor` reference.
- [X] 5. All existing functionality related to command execution and focus changes remains intact.
- [X] 6. Code remains clean, well-documented, and type-hinted.

**Rationale:**
This refactoring aims to:
- Improve separation of concerns: `CommandProcessor` becomes more responsible for the command lifecycle, including focus changes triggered by commands.
- Enhance encapsulation: `CommandContext` receives its dependencies explicitly.
- Centralize related logic: Focus changes, often initiated by commands, are now managed closer to the command execution mechanism.

## Task 6: Implement Immutable State for Command Processing and Refactor AgentEngine

**Status:** Completed

**Description:**
Refactor `AgentEngine` and `CommandProcessor` to use an immutable state pattern for command processing. This enhances predictability and prepares for potential parallelism. Additionally, improve `AgentEngine` structure by breaking down large methods and modifying LLM request handling.

**Acceptance Criteria:**
- [X] 1. **Immutable State for Command Processing:**
    - [X] 1.1. Define a `frozen=True` dataclass `EngineProcessingState` to hold relevant engine control flow and command processing outcomes (e.g., `should_finish`, `root_completion_message`, command execution results).
    - [X] 1.2. Implement `with_...` methods on `EngineProcessingState` using `dataclasses.replace` for immutable updates.
- [X] 2. **Stateless CommandProcessor:**
    - [X] 2.1. Modify `CommandProcessor.process` to accept the current `EngineProcessingState` and return a new `EngineProcessingState`.
    - [X] 2.2. Remove instance variables from `CommandProcessor` that previously held turn-specific state.
    - [X] 2.3. Adapt `CommandProcessor` helper methods (including `focus_up`, `fail_and_focus_up`) to operate with and contribute to the `EngineProcessingState`.
    - [X] 2.4. `CommandContextImpl` updated to facilitate passing necessary state changes (like `should_finish_engine` from focus commands) back to `CommandProcessor`.
- [X] 3. **AgentEngine Manages Immutable State:**
    - [X] 3.1. `AgentEngine.execute` initializes and updates its `EngineProcessingState` based on the output from command processing.
    - [X] 3.2. Control flow in `AgentEngine.execute` (e.g., loop termination) is driven by `EngineProcessingState.should_finish`.
    - [X] 3.3. `AgentEngine` sources its final `root_completion_message` from the terminal `EngineProcessingState`.
- [X] 4. **Refactor `AgentEngine._handle_llm_request`:**
    - [X] 4.1. Method returns the full LLM response string directly (instead of yielding).
    - [X] 4.2. Method re-raises `KeyboardInterrupt` if it occurs.
- [X] 5. **Refactor Long Methods in AgentEngine:**
    - [X] 5.1. Break down `AgentEngine.execute` into smaller, focused private helper methods (e.g., `_prepare_interface_and_history_for_node`, `_compile_history_for_llm`, `_manage_budget`, `_render_auto_reply_block_for_llm`, `_handle_budget_exhaustion`, `_handle_initial_budget_depletion`, `_handle_approaching_budget_warning`).
    - [X] 5.2. Other `AgentEngine` methods (e.g., `add_new_instruction`) are also broken down if overly long (`_create_and_add_new_instruction_message`).
    - [X] 5.3. Aim for helper methods to be around 10-15 lines, promoting clarity and maintainability.

**Rationale:**
Adopting an immutable state pattern for command processing reduces side effects and makes the engine's state transitions more explicit and easier to reason about. This is a crucial step towards enabling more complex features like parallel task execution. Breaking down large methods in `AgentEngine` improves code readability, testability, and adherence to clean code principles ("Uncle Bob's effect").

## Task 7: Creating Task Processor

Currently engine is already split into engine and command processor.
We create one command processor per "cycle" and it processes all the commands from that response.
But the cycles are still in the engine. Because of which engine has to keep track which task is currently active.
Our vision is to allow parallelism, which means the engine should be free from dealing with the execution of a given task.
We already have a task tree structure, which tracks the schedule of the task nodes.
We just need to split the engine again, extract something called a TaskProcessor, which will take a task (TaskTreeNode maybe) and run it until it changes status (either is finished/failed or is pending child tasks).
This way the engine uses the task tree to ask for the "next" task, creates a TaskProcessor for this task, and runs it.
So the engine still has its own cycle, which every time asks for next task and creates a TaskProcessor.
If a task is pending for a child node, TaskProcessor will finish. Then later when the child node has finished, the next() of the task tree will again return the parent node, for which a new TaskProcessor will be created. Which means at different points, for the same task, different instances of TaskProcessor will work. Make sure this will work smoothly.
The implementation should be ready for the future, where the engine will pick multiple tasks and run them in separate threads by creating one TaskProcessor for each in a separate thread.
The TaskProcessor has its own cycle, which runs until the task changes status.
Adjust the command context, command handling in general, to accomodate for this.


- [X] Write HLD markdown file in tasks/7/. Are there any other changes that are going to be required for this?
- [X] Write LLD (Narrative provided, detailed component changes implemented)
- [X] Break down tasks (Implicitly done through HLD/LLD and step-by-step implementation)
- [X] Implement (Core implementation of TaskProcessor, BudgetManager, and refactoring of Engine/CommandProcessor/Context completed)
- [ ] Verify it follows the best practices and code guidelines (Manual review recommended)
