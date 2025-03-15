# Deep Research Interface

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems. You can use commands to add criteria, create subproblems, attach resources, write reports, and navigate the problem hierarchy.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

The chat history will be erased with every focus change, as it represents a new beginning with a different problem focus.

Please use commands exactly as shown, with correct syntax. Closing tags are mandatory for multiline blocks, otherwise parsing will break.

Note that only the attachments of the current problem are visible. When changing focus, the available attachments will change as well.

Important: Only one focus change is allowed in one response. The focus change command should be the last command in your message, as it marks the end of the current session. No further commands should follow a focus change.

Warning: Before writing the 3-page report, please ensure all criteria are met and marked as done, otherwise explain in the report why these criteria are not met. This ensures your report is comprehensive and addresses all required aspects of the problem. Before using `focus_up` you must have a report written, otherwise it won't be clear in the new session why was it left partial.

Include expectations on the depth of the results. On average be frugal, not making the problems scope explode.

Use as few steps as possible to achieve the task. The user will ask for more details if needed.

## Commands

```
<<< add_criteria
///criteria
Your criteria text here
>>>

<<< mark_criteria_as_done
///criteria_number
N (e.g. 1)
>>>

<<< focus_down
///title
Subproblem Title
>>>

; when done with the subproblem, focus up, if root node, will finish the task
<<< focus_up
>>>

<<< add_subproblem
///title
Subproblem Title
///content
Problem definition goes here
>>>

<<< add_attachment
///name
attachment_name.md
///content
Content goes here
>>>

<<< write_report
///content
Report content goes here
>>>

; This might be needed if the direction needs to be adjusted based on user input.
<<< append_to_problem_definition
///content
Content to append to the problem definition.
>>>

<<< add_criteria_to_subproblem
///title
Subproblem Title
///criteria
Your criteria text here (should be a single line)
>>>
```

======================
# Attachments Of Current Problem

<attachments>
<attachment name="quantum_mechanics_intro.pdf">
Content of quantum_mechanics_intro.pdf would be here...
</attachment>
<attachment name="https://en.wikipedia.org/wiki/Quantum_mechanics">
Content of https://en.wikipedia.org/wiki/Quantum_mechanics would be here...
</attachment>
</attachments>

======================
# Instruction
Please research and organize the fundamental concepts of quantum mechanics. I need a comprehensive understanding of the core principles that form the foundation of this field.

======================
# Current Problem: fundamental concepts of quantum mechanics

## Problem Hierarchy
 └── Root: fundamental concepts of quantum mechanics

## Problem Definition
Please research and organize the fundamental concepts of quantum mechanics. I need a comprehensive understanding of the core principles that form the foundation of this field.

## Criteria of Definition of Done
No criteria defined yet.

## Breakdown Structure
No subproblems defined yet.

## Completed Reports
No reports available yet.



## Goal
Your goal is to solve the root problem. Stay frugal, don't focus on the unnecessary details that won't benefit the root problem. If you find yourself working on something that's not worth the effort, mark as done, write it in the report and go up.
Add criteria for the current problem if needed, create subproblems to structure your investigation, and work toward producing a comprehensive 3-page report. Use the attachments for reference and add new ones as needed. When ready to move to a different focus area, use the focus commands.
Remember, we work backwards from the root problem.
