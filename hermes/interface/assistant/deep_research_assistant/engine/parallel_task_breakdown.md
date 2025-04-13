# Task Breakdown: Parallel Subtask Execution

This document breaks down the implementation of parallel subtask execution into smaller, incremental tasks. Each task should result in a functional system state.

**Phase 1: Setup and Configuration**

DECISION: PENDING is enough, no need for another status for parallel
1.  **Task 1.1: Introduce `PENDING_PARALLEL` Status**
    *   **Goal:** Add the new problem status enum value.
    *   **Files:** `file_system.py`, `status_printer.py`, `interface.py`, `hierarchy_formatter.py`
    *   **Changes:**
        *   Add `PENDING_PARALLEL = "PENDING_PARALLEL"` to `ProblemStatus` enum in `file_system.py`.
        *   Update `get_status_emoji` in `Node` (`file_system.py`) to return an appropriate emoji (e.g., 🚦 or ⏳).
        *   Update `StatusPrinter._print_problem_tree` to recognize and print the new status/emoji.
        *   Update `DeepResearcherInterface._format_subproblems` (via `HierarchyFormatter`) and `_format_problem_path_hierarchy` to handle the new status in XML output.
    *   **Verification:** Run the assistant, manually set a node's status to `PENDING_PARALLEL` (via debugger or temporary code), and verify it displays correctly in status prints and interface XML. Functionality remains sequential.

DECISION: Default max_parallel_threads is None, which means no limitation
2.  **Task 1.2: Add `max_parallel_threads` Configuration**
    *   **Goal:** Introduce the configuration setting for parallelism limit, defaulting to 1.
    *   **Files:** `engine.py`, `interface.py`
    *   **Changes:**
        *   Add `max_parallel_threads: int = 1` parameter to `DeepResearchEngine.__init__`. Store it as `self.max_parallel_threads`.
        *   Add corresponding parameter to `DeepResearchAssistantInterface.__init__` and pass it to the engine constructor.
        *   (Optional) Add CLI argument parsing in `main.py` or wherever the interface is instantiated to allow setting this value externally.
    *   **Verification:** The system still runs sequentially as the limit is 1. Verify the setting can be passed through.

3.  **Task 1.3: Add Thread-Safe Budget Counter**
    *   **Goal:** Ensure the budget counter (`message_cycles_used`) is updated atomically.
    *   **Files:** `engine.py`
    *   **Changes:**
        *   Import `threading`.
        *   Add `self.budget_lock = threading.Lock()` in `DeepResearchEngine.__init__`.
        *   Modify `increment_message_cycles` to acquire/release the lock: `with self.budget_lock: self.message_cycles_used += 1`.
    *   **Verification:** Budget counting still works correctly in sequential mode. This prepares for future parallel updates.

**Phase 2: Introduce Core Parallelism Structures (Non-functional)**

4.  **Task 2.1: Introduce Basic `ParallelTaskManager` Structure**
    *   **Goal:** Create the skeleton class for managing parallel tasks.
    *   **Files:** `engine/parallel_task_manager.py` (New File), `engine/engine.py`
    *   **Changes:**
        *   Create `parallel_task_manager.py`.
        *   Define `ParallelTaskManager` class with `__init__(self, max_workers)`. Initialize a `threading.BoundedSemaphore(max_workers)`.
        *   Add placeholder methods: `submit_tasks(self, tasks: List[Node], parent_context)`, `wait_for_completion(self, parent_context)`, `get_results(self, parent_context)`.
        *   In `engine.py`, import `ParallelTaskManager`.
        *   Instantiate `self.task_manager = ParallelTaskManager(self.max_parallel_threads)` in `DeepResearchEngine.__init__`.
    *   **Verification:** System runs sequentially. The new class exists but is not used.

5.  **Task 2.2: Introduce Basic `SubtaskRunner` Structure**
    *   **Goal:** Create the skeleton class/function that will execute individual subtasks.
    *   **Files:** `engine/subtask_runner.py` (New File)
    *   **Changes:**
        *   Create `subtask_runner.py`.
        *   Define a class `SubtaskRunner` or a function `run_subtask`.
        *   It should accept parameters like `node: Node`, `command_context: CommandContext`, `llm_interface: LLMInterface`, `budget_lock: threading.Lock`, `completion_callback`, etc.
        *   Include a placeholder `run()` method or main function body.
    *   **Verification:** System runs sequentially. The new structure exists but is not used.

**Phase 3: Refactor Commands and Engine Logic (Still Sequential)**

6.  **Task 3.1: Refactor `activate_subproblems_and_wait` Command (Sequential Prep)**
    *   **Goal:** Decouple the command from direct sequential execution logic (`focus_down`, `children_queue`). Prepare it to hand off tasks.
    *   **Files:** `commands.py`, `engine.py`
    *   **Changes:**
        *   In `FocusDownCommand.execute`:
            *   Validate subproblems exist.
            *   Set `context.current_node.status = ProblemStatus.PENDING_PARALLEL`.
            *   *Remove* the queuing logic (`context.children_queue[...]`) and the call to `context.focus_down(titles[0])`.
            *   Store the list of target subproblem nodes temporarily (e.g., on the `context` or a new engine attribute) to be picked up by the engine loop.
            *   Keep the `add_output` message.
        *   In `DeepResearchEngine.execute`:
            *   After `process_commands`, check if the status became `PENDING_PARALLEL`.
            *   If so, retrieve the list of target subproblems.
            *   Mimic the *old* `focus_down` behavior for the *first* subproblem in the list (set `self.next_node`, set parent `PENDING`).
            *   Store the *rest* of the subproblems in the *old* `self.children_queue[parent_node.title]` for the existing sequential mechanism to handle upon `focus_up`.
            *   Update files via `self.file_system.update_files()`.
    *   **Verification:** The `activate_subproblems_and_wait` command should still function sequentially, activating the first subproblem and queuing the rest using the old mechanism, but the parent status briefly becomes `PENDING_PARALLEL` before changing back to `PENDING`.

7.  **Task 3.2: Refactor `finish_problem`/`fail_problem` Commands (Sequential Prep)**
    *   **Goal:** Decouple commands from direct focus changes. Introduce signaling.
    *   **Files:** `commands.py`, `engine.py`, `command_context.py`
    *   **Changes:**
        *   Add `completion_requested: Optional[ProblemStatus] = None` to `CommandContext`.
        *   In `FocusUpCommand.execute` (`finish_problem`):
            *   Remove the call to `context.focus_up()`.
            *   Set `context.completion_requested = ProblemStatus.FINISHED`.
        *   In `FailProblemAndFocusUpCommand.execute` (`fail_problem`):
            *   Remove the call to `context.fail_and_focus_up()`.
            *   Set `context.completion_requested = ProblemStatus.FAILED`.
        *   In `DeepResearchEngine.execute`:
            *   After `process_commands`, check `self.command_context.completion_requested`.
            *   If set (e.g., `FINISHED`):
                *   Perform the logic previously in `focus_up` (set current node status, determine `next_node` based on `children_queue` or parent, set `self.finished` if root, add internal message to parent).
            *   If set (e.g., `FAILED`):
                *   Perform the logic previously in `fail_and_focus_up` (set current node status, determine `next_node` as parent, set `self.finished` if root, add internal message to parent).
            *   Reset `self.command_context.completion_requested = None`.
            *   Update files.
    *   **Verification:** `finish_problem` and `fail_problem` should still work sequentially, triggering the correct focus changes via the engine loop after command processing.

**Phase 4: Implement Basic Parallel Execution (Limit 1)**

8.  **Task 4.1: Implement Core `SubtaskRunner` Logic**
    *   **Goal:** Move the single-node execution loop into the `SubtaskRunner`.
    *   **Files:** `engine/subtask_runner.py`, `engine.py`
    *   **Changes:**
        *   In `subtask_runner.py`:
            *   Flesh out the `SubtaskRunner.run` method (or `run_subtask` function).
            *   This loop should largely mirror the main loop in `DeepResearchEngine.execute` *but only for a single node*:
                *   Render interface sections relevant to *its* node.
                *   Manage *its own* `ChatHistory` interaction (using the node's title).
                *   Generate/send LLM requests using the passed `llm_interface`.
                *   Call `process_commands` (needs careful context passing).
                *   Increment budget using the passed lock (`with budget_lock:`).
                *   Check for completion signals (`context.completion_requested`) set by `finish/fail` commands.
                *   The loop continues until completion is signaled.
                *   Return the final status (`FINISHED` or `FAILED`).
        *   In `engine.py`: Extract the single-node processing logic from the `execute` loop into a helper method or directly into the `SubtaskRunner`. The main `execute` loop will become simpler.
    *   **Verification:** System still runs sequentially, but the core logic for processing a node is now encapsulated in `SubtaskRunner`.

9.  **Task 4.2: Integrate `ParallelTaskManager` (Limit 1)**
    *   **Goal:** Connect the engine, commands, and runner via the task manager, but keep concurrency disabled.
    *   **Files:** `engine.py`, `commands.py`, `engine/parallel_task_manager.py`, `engine/subtask_runner.py`
    *   **Changes:**
        *   In `ParallelTaskManager`:
            *   Implement `submit_tasks`: For each task (Node), acquire the semaphore, create a `SubtaskRunner` instance, create and start a `threading.Thread` targeting the runner's `run` method. Store thread references.
            *   Implement basic `wait_for_completion`: Use `thread.join()` for all submitted threads in the batch.
            *   Implement basic `get_results`: Return collected statuses.
        *   In `FocusDownCommand.execute` (`activate_subproblems_and_wait`):
            *   Instead of storing tasks temporarily, call `context._engine.task_manager.submit_tasks(subproblem_nodes, context)`.
        *   In `DeepResearchEngine.execute`:
            *   If `current_node.status == PENDING_PARALLEL`:
                *   Call `self.task_manager.wait_for_completion(self.command_context)`.
                *   Call `self.task_manager.get_results(...)` (placeholder for now).
                *   Change `current_node.status` back to `IN_PROGRESS`.
                *   (Remove the sequential fallback logic added in Task 3.1).
            *   If not `PENDING_PARALLEL`, call the `SubtaskRunner` logic directly for the `current_node` (as implemented in Task 4.1).
        *   Ensure `SubtaskRunner` receives all necessary context (engine references, locks, etc.).
    *   **Verification:** System should still run *sequentially* because `max_parallel_threads` is 1 (the semaphore allows only one thread at a time). This tests the threading structure and handoffs. `finish/fail` commands within the runner should correctly terminate its loop and allow the `wait_for_completion` to finish.

**Phase 5: Enable Concurrency and Refine**

10. **Task 5.1: Implement Thread-Safe `ChatHistory`**
    *   **Goal:** Protect `ChatHistory` data structures during concurrent access.
    *   **Files:** `history.py`
    *   **Changes:**
        *   Import `threading`, `defaultdict`.
        *   Add `self.node_locks = defaultdict(threading.Lock)` to `ChatHistory.__init__`.
        *   In `add_message`, `get_auto_reply_aggregator`, `commit_and_get_auto_reply`, `clear_node_history`, `get_compiled_blocks`: Acquire the specific lock `with self.node_locks[node_title]:` before accessing/modifying `self.node_blocks[node_title]` or `self.node_auto_reply_aggregators[node_title]`.
    *   **Verification:** Run with `max_parallel_threads = 1`. Ensure history still works. Prepare for >1.

11. **Task 5.2: Implement LLM Interface Locking**
    *   **Goal:** Serialize LLM calls if the underlying client is not thread-safe or to manage API limits.
    *   **Files:** `engine.py`, `engine/subtask_runner.py`, `llm_interface_impl.py` (potentially)
    *   **Changes:**
        *   Add `self.llm_lock = threading.Lock()` in `DeepResearchEngine.__init__`.
        *   Pass this lock to `SubtaskRunner`.
        *   In `SubtaskRunner.run`, wrap the call to `self.llm_interface.send_request(...)` and subsequent processing within `with self.llm_lock:`.
        *   (Optional) Investigate if `ChatModelLLMInterface` or specific model clients *are* thread-safe. If so, this lock might be conditional or unnecessary, but adding it provides safety.
    *   **Verification:** Run with `max_parallel_threads = 1`. Ensure LLM calls still work.

12. **Task 5.3: Enable Actual Parallelism (Increase Limit)**
    *   **Goal:** Allow concurrent execution by increasing the thread limit.
    *   **Files:** `engine.py` (or CLI/config)
    *   **Changes:**
        *   Change the default or configured `max_parallel_threads` to > 1 (e.g., 4).
    *   **Verification:** Observe concurrent execution (e.g., via logging/print statements in `SubtaskRunner`). Monitor for deadlocks, race conditions, or unexpected behavior. Test with multiple subtasks activated simultaneously.

13. **Task 5.4: Implement Result Aggregation and Reporting**
    *   **Goal:** Collect results from parallel tasks and report them back to the parent node.
    *   **Files:** `engine/parallel_task_manager.py`, `engine/subtask_runner.py`, `engine.py`, `history.py`
    *   **Changes:**
        *   In `SubtaskRunner`: When finishing, collect relevant outputs (e.g., final status, errors, key artifacts created, command outputs generated during its run).
        *   In `ParallelTaskManager`: Store results reported by each completed `SubtaskRunner`. Modify `get_results` to return this aggregated data.
        *   In `DeepResearchEngine.execute`: When `wait_for_completion` finishes:
            *   Call `get_results`.
            *   Format a summary message (e.g., "Subtask X finished: [Status]. Subtask Y failed: [Error]...").
            *   Use the *parent* node's `AutoReplyAggregator` (`self.chat_history.get_auto_reply_aggregator(self.current_node.title)`) to add this summary as an internal message (`add_internal_message_from`).
            *   Potentially aggregate command outputs from children into the parent's auto-reply as well.
    *   **Verification:** Activate multiple subtasks in parallel. After they complete, check the parent node's next auto-reply for the aggregated summary message.

14. **Task 5.5: Refine UI/Status Reporting for Parallelism**
    *   **Goal:** Improve visual feedback for parallel operations.
    *   **Files:** `status_printer.py`, `interface.py`, `hierarchy_formatter.py`
    *   **Changes:**
        *   Modify `StatusPrinter._print_problem_tree` to potentially list active subtasks under a `PENDING_PARALLEL` node. (Requires `ParallelTaskManager` to expose active task info).
        *   Modify `HierarchyFormatter` (`format_subproblems`, `format_problem_path_hierarchy`) to visually distinguish subtasks running in parallel under a `PENDING_PARALLEL` parent in the XML interface output.
    *   **Verification:** Run with parallel tasks and observe the updated status prints and interface XML reflecting the concurrent activity.

15. **Task 5.6: Final Locking Review (`FileSystem`)**
    *   **Goal:** Ensure comprehensive thread safety for file system operations.
    *   **Files:** `file_system.py`
    *   **Changes:**
        *   Rigorously review all methods in `FileSystem` that modify the node tree (`add_subproblem`, `add_artifact`) or interact with the disk (`_write_node_to_disk`, `_create_node_directories`, `update_files`, `add_external_file`).
        *   Ensure `with self.lock:` is used appropriately around all critical sections modifying shared state or performing file I/O. Pay special attention to methods called recursively or those modifying parent/child relationships.
    *   **Verification:** Code review and stress testing with high parallelism (`max_parallel_threads` > 4) involving frequent file/node modifications.

This breakdown provides a step-by-step path, starting with setup, introducing structures, refactoring sequentially, enabling basic threading, and finally adding full concurrency and refinement.

---

## Review Notes (2025-04-14)

Based on a review of the current codebase and design (`parallel.md`):

1.  **`PENDING_PARALLEL` Status (Task 1.1):** This task is obsolete based on the decision noted ("PENDING is enough"). The focus should be on ensuring the `PENDING` status is correctly used and reported when waiting for parallel tasks.
2.  **Command Refactoring & Signaling (Tasks 3.1, 3.2):**
    *   The core refactoring to use signals (`completion_requested`, `pending_subproblems_to_activate` in `CommandContext`) is **DONE**.
    *   Task 3.1 description needs update: The `activate_subproblems_and_wait` command now sets the `pending_subproblems_to_activate` signal. The engine loop detects this *after* command processing, sets the parent to `PENDING`, and interacts with the `ParallelTaskManager`. The sequential fallback/`children_queue` logic mentioned is no longer relevant here.
    *   Task 3.2 description (using `completion_requested`) is accurate to the current implementation.
3.  **Engine Loop Integration (Task 4.2):** The trigger mechanism is the `pending_subproblems_to_activate` signal, not checking for a specific status *before* command processing. The engine loop should:
    *   Process commands.
    *   Check for `completion_requested` signal -> handle finish/fail.
    *   Check for `pending_subproblems_to_activate` signal -> set parent `PENDING`, call `task_manager.submit_tasks`, clear signal.
    *   If the *current* node's status *is* `PENDING` (set in a previous cycle), call `task_manager.wait_for_completion`, process results, set status back to `IN_PROGRESS`.
    *   Otherwise (normal sequential step), run the single node logic (potentially via `SubtaskRunner`).
4.  **Missing/Incomplete Tasks:**
    *   **Context Propagation:** Need explicit steps/verification for passing shared resources (LLM interface, file system, chat history, locks) to `ParallelTaskManager` and `SubtaskRunner`.
    *   **Locking Implementation:**
        *   Task 5.1 (`ChatHistory` locking): **Needs Implementation.**
        *   Task 5.2 (`LLMInterface` locking): **Needs Implementation.**
        *   Task 5.6 (`FileSystem` locking): Should be changed to **Verify Existing Lock Usage.** The `RLock` exists, but its application needs review for parallel scenarios.
    *   **Result Aggregation (Task 5.4):** **Needs Implementation.** Define how results are passed from `SubtaskRunner` -> `ParallelTaskManager` -> Parent `AutoReplyAggregator`.
    *   **UI/Status Reporting (Task 5.5):** **Needs Implementation.** Adapt `StatusPrinter` and `HierarchyFormatter` for `PENDING` status when parallel tasks are active.
    *   **SubtaskRunner Implementation (Task 4.1 & 4.2):** Needs detailed implementation, ensuring it correctly uses passed context/locks and handles its lifecycle based on signals.
