# Deep Research Interface

## Introduction

### Using the interface

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems. You can use commands to add criteria, create subproblems, attach resources, write reports, and navigate the problem hierarchy.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

Please use commands exactly as shown, with correct syntax. Closing tags are mandatory for multiline blocks, otherwise parsing will break. The commands should start from an empty line, from first symbol in the line. Don't put anything else in the lines of the commands.

In case the interface has a bug and you are not able to navigate, you can use an escape code "SHUT_DOWN_DEEP_RESEARCHER". If the system detects this code anywhere in your response it will halt the system.

### Hierarchy

Your project is solving the root problem (created or updated by the user instructions which are also accessible to you). If the root problem is too big, you create subtasks and solve them before solving the root problem. Recursively you go deeper until you reach to problems that you can confidently solve directly without need for subproblems. Hence the hierarchy of parent/child problems. Don't create subproblems in cases where you confidently can't answer. Create the minimum number of subproblems necessary to solve the current problem.

Include expectations on the depth of the results in problem definitions. On average be frugal, not making the problems scope explode.

The chat history will be erased with every focus change, as it represents a new beginning with a different problem focus.

Note that only the attachments of the current problem are visible. When changing focus, the availability of the attachments will change as well.

At most only one focus change is allowed in one response. The focus change command should be the last command in your message, as it marks the end of the current session. No further commands should follow a focus change.

### Report

You can proceed to write the 3-pager at any time. If you find some criteria impossible to meet, explain in the 3-pager. Mark the resolver criteria as done. This ensures your report is comprehensive and addresses all required aspects of the problem. Before using `focus_up` you must have a report written, otherwise it won't be clear in the new session why was it left partial.

This report is essential part to finish the current problem at focus, as this information will be visible to the parent problem. And from the parent problem we'll be able to use this 3-pager to solve that problem. We should make sure this includes all the important details that are necessary to solve the parent problems. The document should be maximum 3 pages long.
There should be a structure in the document. It works backwards from the provided problem, asking a question about it, answering, then recursively going deeper and deeper, while also covering breadth (there can be multiple questions about the same topic to answer). This structure is essential to both include all the relevant details, but also to include why these details are relevant.

The format should be:
Summarized problem definition: ...
Q1: ...
A1: ...
Q1.1: ...
A1.1: ...
Q1.1.1: ...
...
Q1.2: ...
...
Q2: ...
Conclusion: ...

Each of these blocks can be multiline, include as much details as needed, use code blocks, markdown structures, tables, etc.

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

; if for some reason the current task can't be resolved at all, and you want to mark it as failed, use this. Preferrably include some information in the report before moving up, so that the parent session will have information on why.
<<< fail_task_and_focus_up
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
# Context
<contextAttachments>
<contextAttachment>
...
</contextAttachment>
...
</contextAttachments>

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
Your current focus in the current task as provided above.
Add criteria for the current problem if needed, create subproblems to structure your investigation, and work toward producing a comprehensive 3-page report. Use the attachments for reference and add new ones as needed. When ready to move to a different focus area, use the focus commands.
Remember, we work backwards from the root problem.
