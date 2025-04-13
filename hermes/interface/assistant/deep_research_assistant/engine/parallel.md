# Design Doc: Parallel Subtask Execution in Deep Research Assistant

**1. Introduction**

This document outlines the design for enabling parallel execution of subtasks within the Deep Research Assistant using multithreading. The goal is to allow multiple subproblems, activated via the `activate_subproblems_and_wait` command, to run concurrently, potentially improving overall research throughput. The design includes a mechanism to limit the degree of parallelism via a configurable setting.

**2. Current State**

*   The `activate_subproblems_and_wait` command accepts multiple subproblem titles.
*   The `DeepResearchEngine` currently uses a `children_queue` to manage these subproblems.
*   When a subproblem finishes (`finish_problem` or `fail_problem`), the engine checks the queue for the parent and activates the next subproblem sequentially.
*   The engine processes one `current_node` at a time in its main `execute` loop.
*   Focus shifts (`focus_up`/`focus_down`) manage the sequential flow between parent and child nodes.
*   Shared resources like `FileSystem` (using an `RLock`), `ChatHistory`, and `LLMInterface` exist.

**3. Goals**

*   Execute multiple subtasks, activated by a single `activate_subproblems_and_wait` command, concurrently using Python's `threading` module.
*   Introduce a configurable limit (`max_parallel_threads`) to control the maximum number of concurrently running subtask threads.
*   Ensure thread safety for all shared resources accessed by concurrent threads.
*   Maintain coherent state management, status reporting, and result aggregation.
*   Adapt budget tracking to accurately reflect work done across parallel threads.

**4. Challenges**

*   **Concurrency Control:** Ensuring thread-safe access to shared objects:
    *   `FileSystem`: Writing files, creating directories, modifying the node tree structure (adding/removing nodes, artifacts). The existing `RLock` needs careful review for comprehensive coverage.
    *   `ChatHistory`: Appending messages/autoreplies to `node_blocks`, updating `node_auto_reply_aggregators`. `defaultdict` itself isn't sufficient for concurrent list/dict modifications.
    *   `Node` objects: Modifying lists (`criteria`, `criteria_done`) or dicts (`artifacts`, `subproblems`, `visible_artifacts`) within a node instance. While each thread should primarily work on its *own* node, commands might interact with other nodes (e.g., `open_artifact`).
    *   Budget Counter (`message_cycles_used`): Needs atomic updates.
    *   `LLMInterface`: Underlying clients or APIs might have concurrency limits or non-thread-safe state.
*   **Engine State Management:** The engine's main loop and state (`current_node`) are designed for sequential execution. This needs redesigning to manage and wait for multiple concurrent tasks.
*   **LLM Interaction:** Each parallel thread needs to manage its LLM request/response cycle independently. Potential for increased costs and hitting API rate limits.
*   **Completion Detection:** Determining when *all* subtasks initiated by a specific parent command have finished (successfully or failed).
*   **User Interface & Reporting:** How to represent the status of parallel tasks? How to aggregate outputs and errors from multiple threads back to the parent context?
*   **Error Handling:** How should an error in one thread affect others in the same batch? How are errors reported?
*   **Focus Management:** The `focus_up`/`focus_down` logic and the `children_queue` are inherently sequential and need replacement.

**5. Proposed Design**

*   **5.1. Introduce `ParallelTaskManager`:**
    *   A new class, likely managed by `DeepResearchEngine`.
    *   Responsibilities:
        *   Receive lists of subtasks to run from the `activate_subproblems_and_wait` command.
        *   Manage a `threading.BoundedSemaphore` or similar mechanism to enforce the `max_parallel_threads` limit.
        *   Launch `SubtaskRunner` instances in separate threads.
        *   Track active threads and their associated parent activation request.
        *   Collect results (status, outputs, errors) from completed threads.
        *   Use synchronization primitives (e.g., `threading.Event`, `threading.Condition`, counters) to wait for all threads in a batch to complete.
        *   Signal the main engine when a batch is complete.
*   **5.2. Introduce `SubtaskRunner`:**
    *   A new class or function designed to be the target of each subtask thread.
    *   Each instance/call receives the specific `Node` object for the subproblem it needs to run.
    *   It contains the core research loop for that single node:
        *   Render interface sections relevant to its node.
        *   Interact with `ChatHistory` using appropriate locks.
        *   Generate and send LLM requests via `LLMInterface` (potentially serializing calls through a lock if needed).
        *   Process commands using a `CommandContext` (which still references the shared engine components but operates within the thread's context).
        *   Increment the shared, locked budget counter (`message_cycles_used`) after each LLM cycle.
        *   Handle `finish_problem`/`fail_problem`: Instead of changing engine focus directly, it reports its completion status (success/failure) and any relevant output/artifacts back to the `ParallelTaskManager`.
        *   Handle recursive `activate_subproblems_and_wait`: It calls back to the `ParallelTaskManager` to queue/run nested parallel tasks.
*   **5.3. Modify `DeepResearchEngine`:**
    *   Add `max_parallel_threads` configuration (e.g., initialized to 1 or 2).
    *   Instantiate and hold a `ParallelTaskManager`.
    *   Modify the main `execute` loop:
        *   If the current node's status is `PENDING_PARALLEL`, the loop waits for a signal from the `ParallelTaskManager` indicating batch completion.
        *   Upon receiving the signal, it processes the aggregated results (updates parent auto-reply, changes parent status back to `IN_PROGRESS`).
        *   If not waiting for parallel tasks, it proceeds with the single active node as before (but potentially using the `SubtaskRunner` logic for consistency).
    *   Remove the `children_queue`.
    *   Implement thread-safe access to `message_cycles_used` using a `threading.Lock`.
*   **5.4. Modify Commands:**
    *   `activate_subproblems_and_wait`:
        *   Validates subproblem existence.
        *   Sets the parent node's status to `PENDING_PARALLEL`.
        *   Passes the list of subproblem nodes to the `ParallelTaskManager` to initiate execution.
        *   No longer directly manipulates `next_node` or `children_queue`.
    *   `finish_problem` / `fail_problem`:
        *   When executed within a `SubtaskRunner` thread, these commands signal completion and status to the `ParallelTaskManager`.
        *   They no longer directly trigger `focus_up` logic in the engine.
*   **5.5. Add `ProblemStatus.PENDING_PARALLEL`:**
    *   A new status in the `ProblemStatus` enum to indicate a node is waiting for its concurrently running children.
*   **5.6. Enhance Thread Safety:**
    *   **`FileSystem`:** Rigorously review all methods modifying the file system or node structure (`_write_node_to_disk`, `_create_node_directories`, `add_artifact`, `add_subproblem`, etc.) and ensure they acquire the `RLock`.
    *   **`ChatHistory`:** Implement fine-grained locking. A `defaultdict(threading.Lock)` could provide a lock per `node_title` to protect access to `node_blocks[node_title]` and `node_auto_reply_aggregators[node_title]`. Acquire the lock before appending/modifying the list/aggregator for a specific node.
    *   **`LLMInterface`:** Default assumption: not thread-safe. The `ParallelTaskManager` or `SubtaskRunner` should use a shared `threading.Lock` to serialize calls to `llm_interface.send_request` if the underlying implementation (e.g., `ChatModelLLMInterface`) cannot handle concurrent requests safely or if API limits require it.
    *   **Budget Counter:** Wrap `self.message_cycles_used += 1` in `SubtaskRunner` with `with self.budget_lock:`.
*   **5.7. Reporting and UI:**
    *   `StatusPrinter` / `interface.py`: Update formatting logic to recognize `PENDING_PARALLEL` status and potentially list the subtasks being run concurrently under that parent.
    *   `AutoReply`: Results (command outputs, errors, internal messages like "Task marked FINISHED") from child threads should be collected by the `ParallelTaskManager`. When the batch completes, the manager should format an aggregated summary and add it as a single internal message or structured report to the *parent* node's `AutoReplyAggregator`.

**6. Estimated File Changes**

*   **`hermes/interface/assistant/deep_research_assistant/engine/engine.py`**: (Major) Integrate `ParallelTaskManager`, modify `execute` loop, add `max_parallel_threads`, manage `PENDING_PARALLEL` state, add budget lock.
*   **`hermes/interface/assistant/deep_research_assistant/engine/commands.py`**: (Moderate) Rewrite `activate_subproblems_and_wait`, `finish_problem`, `fail_problem` logic for parallel context.
*   **`hermes/interface/assistant/deep_research_assistant/engine/file_system.py`**: (Minor) Add `ProblemStatus.PENDING_PARALLEL`, review/ensure lock usage.
*   **`hermes/interface/assistant/deep_research_assistant/engine/history.py`**: (Moderate) Add locking for `node_blocks` and `node_auto_reply_aggregators`.
*   **`hermes/interface/assistant/deep_research_assistant/engine/interface.py`**: (Minor) Update rendering for `PENDING_PARALLEL` status.
*   **`hermes/interface/assistant/deep_research_assistant/engine/status_printer.py`**: (Minor) Update printing for `PENDING_PARALLEL` status.
*   **`hermes/interface/assistant/deep_research_assistant/llm_interface_impl.py`**: (Potential Minor) May need adjustments if LLM client instances need to be managed differently or if serialization lock is added around `send_request`.
*   **New File:** `hermes/interface/assistant/deep_research_assistant/engine/parallel_task_manager.py` (or similar name).
*   **New File:** `hermes/interface/assistant/deep_research_assistant/engine/subtask_runner.py` (or similar name).

**7. Open Questions / Future Considerations**

*   How to handle cancellation of in-progress parallel tasks?
*   Detailed strategy for error propagation from child threads to the parent.
*   Refining the aggregation and presentation of results from parallel tasks in the parent's auto-reply.
*   Performance tuning of `max_parallel_threads`.
*   Ensuring any external commands used are thread-safe or appropriately locked.