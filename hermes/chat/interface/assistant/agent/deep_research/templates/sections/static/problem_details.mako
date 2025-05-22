<%namespace name="xml" file="/macros/xml.mako"/>

${'##'} Workflow

${'###'} Subproblems (Parallel Execution)

When creating subproblems:
1. Use `activate_subproblems` to queue them for parallel execution
2. Use `wait_for_subproblems` to pause until specific ones complete
3. Monitor status through dynamic sections
4. Budget is shared across all parallel tasks

Key expectations:
- Design subproblems as independent units for maximum parallelism
- Combine related commands in single messages to reduce roundtrips
- Balance depth vs breadth - shallow hierarchies enable more parallelism
- Artifacts from parallel subproblems are automatically visible

${'###'} Depth

Depth is how far we are from the root problem.
Root problem has a depth of 0.
Subproblems of the root problem has a depth of 1. Etc.
As a rule of thumn, unless really necessary, don't go below depth 3.

${'###'} Problem Status System

Each problem in the hierarchy has a status that indicates its current state:
- **CREATED**: A problem that has been created but not yet activated
- **READY_TO_START**: After being created, it has been marked as created
- **PENDING**: A problem that is temporarily paused because it awaits the results of its subproblems
- **IN_PROGRESS**: The problem that is being currently worked on
- **FINISHED**: A problem that has been successfully completed
- **FAILED**: A problem that could not be solved or was determined to be unsolvable
- **CANCELLED**: A problem that was determined to be unnecessary or irrelevant

You can see the status of each problem in the breakdown structure.

${'###'} Log Management

The `add_log_entry` command allows you to log permanent, one-sentence summaries of key actions or milestones in the Permanent Logs section. Its purpose is to maintain a clear, concise record of progress across all problems, ensuring the overall progress is always visible. This is crucial because it helps you stay aligned with the root problem's goals, avoids redundant work, and provides context for reports or navigation. Use it whenever you take actions - like creating a subtask, adding an artifact, or finishing a problem - to document outcomes that matter to the hierarchy. Add entries right after the action, keeping them specific and brief (e.g., "Artifact 1 artifact created in task with title ..." rather than "Did something"). This keeps the history actionable and relevant.
