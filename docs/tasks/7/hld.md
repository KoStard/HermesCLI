# High-Level Design: TaskProcessor Refactoring (Task 7)

## 1. Introduction

The current `AgentEngine` is responsible for both the overall orchestration of the research process (managing the task tree, budget, etc.) and the detailed execution of individual research tasks (LLM interactions, command processing within a task). This monolithic design makes it difficult to introduce parallelism for task execution and blurs the separation of concerns regarding the lifecycle management of a single task versus the entire research project.

Task 7 aims to refactor this by extracting the logic for executing a single research task into a new, dedicated component: `TaskProcessor`.

## 2. Goals

*   **Isolate Task Execution:** Encapsulate the execution logic for a single `ResearchNode` (represented by a `TaskTreeNode`) within a `TaskProcessor` class.
*   **Decouple Engine from Task Details:** Allow `AgentEngine` to focus on higher-level orchestration, such as selecting the next task from the `TaskTree` and managing `TaskProcessor` instances.
*   **Facilitate Parallelism:** Lay the groundwork for future concurrent execution of multiple tasks by making `TaskProcessor` the unit of parallel work.
*   **Improve Separation of Concerns:** Clearly distinguish between managing the lifecycle of an individual task and managing the overall research project.
*   **Maintain Functionality:** Ensure all existing research capabilities, command behaviors, and state management (including budget) remain intact.

## 3. Proposed Solution

The core idea is to introduce a `TaskProcessor` that takes a `TaskTreeNode` and runs it until its status changes significantly (e.g., it's finished, failed, or becomes pending due to child task creation).

### 3.1. `TaskProcessor` (New Class)

*   **Responsibilities:**
    *   Manages the execution lifecycle of a single `TaskTreeNode`.
    *   Contains the primary loop for interacting with the LLM, processing commands, updating task history, and managing the task's state.
*   **Constructor Dependencies:**
    *   `task_tree_node: TaskTreeNode` (the specific task it will process)
    *   `research: Research` (access to shared project components like KB, permanent logs, external files)
    *   `llm_interface: LLMInterface`
    *   `command_registry: CommandRegistry`
    *   `command_context_factory: CommandContextFactory`
    *   `template_manager: TemplateManager`
    *   `renderer_registry: DynamicDataTypeToRendererMap`
    *   `agent_interface: AgentInterface`
    *   `status_printer: StatusPrinter`
    *   `budget: BudgetManager` (or similar mechanism for global budget tracking and updates)
*   **Key Method: `run()`:**
    *   This method will contain an internal loop, similar to the current main loop in `AgentEngine.execute()`.
    *   The loop continues as long as its assigned `TaskTreeNode` is active and not yet finished, failed, or pending children that require the engine to switch focus (as determined by `TaskTree`).
    *   **Inside the `run()` loop (for each cycle of its assigned task):**
        1.  Retrieve the `ResearchNode` from its `TaskTreeNode`.
        2.  Prepare the interface and history for the `ResearchNode` (similar to `AgentEngine._prepare_interface_and_history_for_node`). This includes rendering dynamic sections and managing the `AutoReplyAggregator`.
        3.  Compile the historical messages for the LLM (similar to `AgentEngine._compile_history_for_llm`).
        4.  Make the LLM request (similar to `AgentEngine._handle_llm_request`).
        5.  Instantiate a `CommandProcessor`.
        6.  Process commands from the LLM response using `commandProcessor.process()`. This will use an `EngineProcessingState` (or a more aptly named `TaskProcessingState`) to capture the outcome of command execution for this specific cycle.
        7.  Update the global budget (e.g., via `budget_manager.increment_message_cycles()`) and check for exhaustion (`budget_manager.manage_budget()`). If budget exhaustion signals a global stop, `run()` should terminate and indicate this.
        8.  Save the `ResearchNode`'s history.
        9.  Print the current status using `status_printer`.
        10. Check the `ResearchNode`'s status. If it's `FINISHED`, `FAILED`, or has become `PENDING` (due to `focus_down`), the `TaskProcessor.run()` method should return, signaling its completion for this `TaskTreeNode` instance.
*   **Statelessness:** Each `TaskProcessor` instance is created for a specific `TaskTreeNode` when it's time to process it. It should not hold state beyond its execution run. All persistent changes are saved to the `ResearchNode` and its components.

### 3.2. `AgentEngine` (Modified)

*   **Responsibilities:**
    *   Overall research project orchestration.
    *   Initializing the `Research` object (including loading existing research).
    *   Defining the root problem and initializing the `TaskTree`.
    *   Managing the main execution flow:
        *   Looping as long as `TaskTree.next()` provides a `TaskTreeNode`.
        *   For each active `TaskTreeNode`:
            *   Instantiating a new `TaskProcessor` with all necessary dependencies.
            *   Calling `task_processor.run()`.
    *   Managing the global budget (instantiating and providing the `BudgetManager` or similar).
    *   Handling the generation of the final research report once all tasks are completed.
*   **`execute()` Method (Refactored):**
    *   The existing detailed LLM interaction loop will be removed.
    * It will now primarily consist of:
      ```python
      # Simplified conceptual flow
      while True:
          current_task_tree_node = self.task_tree.next()
          if current_task_tree_node is None:
              # All tasks completed
              self.final_root_completion_message = ... # (Need to decide how this is set if root finishes)
              break # Exit main loop

          task_processor = TaskProcessor(
              current_task_tree_node,
              self.research,
              self._llm_interface,
              self.command_registry,
              self.command_context_factory,
              self.template_manager,
              self.renderer_registry,
              self.interface, # AgentInterface
              self.status_printer,
              self.budget_manager # or self directly if it manages budget
          )
          task_processor.run()

          if self.budget_manager.is_globally_exhausted_and_stop_signaled(): # example
               break
      
      # Final reporting, etc.
      print("Engine execution complete. Awaiting new instruction or shutdown.")
      ```
*   **Budget Finalization:** The `final_root_completion_message` and overall `should_finish` logic (if the root node processing within a `TaskProcessor` decided the whole research should conclude) needs to be communicated back to the `AgentEngine`. `TaskProcessor.run()` could return a status object.

### 3.3. `CommandProcessor` (Usage Change)

*   Instantiated by `TaskProcessor` for each LLM response cycle within that task's processing.
*   The `EngineProcessingState` (or `TaskProcessingState`) it uses and returns will reflect the outcome of command execution for *that specific cycle* of the task being processed.
*   The `focus_up`/`fail_and_focus_up` methods in `CommandProcessor` will modify the state of the `ResearchNode` (and thus the `TaskTreeNode`). These changes will be detected by the `TaskProcessor`'s `run()` loop to determine if it should yield control.

### 3.4. `CommandContextImpl` (Modified Dependencies)

*   Its constructor will receive dependencies from the `TaskProcessor` or directly the specific components it needs (e.g., the current `ResearchNode`, the `Research` object, `AutoReplyAggregator`).
*   Instead of `self._engine.some_method()`, it will use, for example, `self.research_object.get_permanent_logs()` or `self.current_research_node.get_history().get_auto_reply_aggregator()`.
*   The `CommandContextFactory` will be responsible for creating this context with the correct dependencies provided by the `TaskProcessor`.

### 3.5. `EngineProcessingState` (Scope Clarification)

*   This dataclass will represent the state/outcome of a *single command processing phase* in response to one LLM message.
*   Used by `CommandProcessor.process()` and interpreted by `TaskProcessor` to update its internal state for the current task cycle.
*   Flags like `should_finish` and `root_completion_message` set by commands (via context) would signal to the `TaskProcessor` that its current `TaskTreeNode` has reached a terminal state or produced a root message. The `TaskProcessor` then acts accordingly (e.g., returns from its `run()` method).

### 3.6. Budget Management

*   A `BudgetManager` (or similar mechanism, possibly methods within `AgentEngine` passed as callbacks or an object) will handle global budget.
*   `AgentEngine` initializes and owns the budget.
*   `TaskProcessor` is given access to this budget manager.
*   Each LLM cycle invoked by a `TaskProcessor` will call `budget_manager.increment_message_cycles()`.
*   `budget_manager.manage_budget()` (containing warnings, buffer logic, user prompts for extension) is called by `TaskProcessor`.
*   If `manage_budget` determines a hard stop, it signals this, and `TaskProcessor.run()` returns, propagating the stop signal if necessary for `AgentEngine` to halt.

## 4. Key Component Interactions Flow

1.  `AgentEngine.execute()` starts.
2.  `AgentEngine` calls `self.task_tree.next()` to get the `current_task_tree_node`.
3.  If `None`, all tasks are done; `AgentEngine` proceeds to final reporting/cleanup.
4.  Else, `AgentEngine` instantiates `task_processor = TaskProcessor(current_task_tree_node, ...all_dependencies...)`.
5.  `AgentEngine` calls `task_processor.run()`.
    *   `TaskProcessor.run()` enters its internal loop (for the lifetime of `current_task_tree_node`'s active processing).
        *   Gets `research_node` from `current_task_tree_node`.
        *   Calls `agent_interface.render_problem_defined(...)`.
        *   Calls `llm_interface.send_request(...)` -> `llm_response`.
        *   Updates and checks global budget via `budget_manager`. If budget forces stop, `task_processor.run()` returns early with a signal.
        *   Instantiates `cmd_processor = CommandProcessor(...)`.
        *   Calls `cmd_processor.process(llm_response, ..., current_engine_processing_state)` -> `new_engine_processing_state`.
            *   `CommandProcessor` calls `command.execute(context, args)`.
            *   `CommandContext` interacts with `research_node` components (history, artifacts, criteria) and `research` components (KB, permanent logs). Focus commands update `research_node` status and `TaskTreeNode` state indirectly via `CommandProcessor` methods.
        *   Saves `research_node.history`.
        *   Prints status via `status_printer`.
        *   Checks `research_node.get_problem_status()` and `new_engine_processing_state.should_finish` (for the node). If node is finished/failed/pending children, `task_processor.run()` loop breaks.
    *   `task_processor.run()` returns (possibly with a status indicating why it returned).
6.  `AgentEngine` loops back to step 2 to get the next task.

## 5. Impact on Existing Components

*   **`AgentEngine`**: Major refactor. Its primary `execute` loop delegates task processing to `TaskProcessor`. Many private helper methods related to single task cycle execution (LLM interaction, command processing loop, per-cycle history prep) will move to `TaskProcessor`.
*   **`CommandContextImpl`**: Constructor changes to accept different dependencies (likely from `TaskProcessor`). Internal calls will change from `_engine.foo` to `self.dependency.foo`.
*   **`CommandProcessor`**: Internal logic for `process` largely similar, but it's instantiated and driven by `TaskProcessor`. Its focus methods (`focus_up`, `fail_and_focus_up`) will be critical for signaling state changes of the `ResearchNode` back to the `TaskProcessor`.
*   **`ResearchNode` / `TaskTreeNode`**: State updates (e.g., `ProblemStatus`, `TaskTreeNode.finish()`) are crucial and will be triggered by commands processed within `TaskProcessor`.
*   **`EngineProcessingState`**: Remains conceptually similar for one command processing cycle but its lifecycle is managed within `TaskProcessor.run()`.

## 6. Threading Model (Future Considerations)

*   `TaskProcessor` instances become the natural units of concurrent work.
*   `AgentEngine` could potentially manage a thread pool and assign ready `TaskTreeNode`s to available `TaskProcessor`s running in separate threads.
*   Shared resources like the `Research` object (and its components like `KnowledgeBase`, `ExternalFilesManager`, `PermanentLogs`) and the `BudgetManager` would require careful thread-safety considerations (e.g., locks, thread-safe collections/methods) if true parallelism is implemented. For this refactoring, sequential execution of `TaskProcessors` by the `AgentEngine` is assumed.

## 7. State Management within TaskProcessor

*   The `TaskProcessor.run()` method will contain the loop that was previously the core of `AgentEngine.execute()`. This loop processes multiple LLM interactions and command execution cycles for its *single assigned TaskTreeNode* until that node's status changes (e.g., `FINISHED`, `FAILED`, or `PENDING` due to newly created child tasks).
*   The `EngineProcessingState` will be used within each iteration of this internal loop in `TaskProcessor.run()` to manage the specific outcomes of commands that were executed in response to a single LLM message.
*   The `TaskProcessor` itself should be created fresh by the `AgentEngine` each time a `TaskTreeNode` becomes active. This ensures it doesn't carry state from previous processing of other nodes or even previous activations of the same node.

## 8. Open Questions/Risks

*   **Dependency Management:** Ensuring `TaskProcessor` gets all necessary dependencies and correctly passes them down to `CommandContextFactory`/`CommandContext` can be complex. Consider a dedicated "context" object for `TaskProcessor` dependencies.
*   **Return State from `TaskProcessor.run()`:** `AgentEngine` needs to know if `TaskProcessor.run()` exited due to task completion, budget exhaustion (requiring global stop), or other reasons. A simple status enum or object might be returned.
*   **`root_completion_message` Handling:** How this message (set when the root node finishes/fails) is reliably passed from a `TaskProcessor` (that processed the root node) back to the `AgentEngine` for the final report.
*   **Testing:** Significant refactoring will require thorough testing of all command paths and research lifecycle scenarios.
*   **Budget Manager Granularity:** Defining the exact interface and responsibility of the `BudgetManager` and how it interacts with `AgentEngine` and `TaskProcessor`.
