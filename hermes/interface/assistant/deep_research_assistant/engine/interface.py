from typing import List, Optional

from .file_system import FileSystem, Node


class DeepResearcherInterface:
    def __init__(self, file_system: FileSystem, instruction: str):
        self.file_system = file_system
        self.instruction = instruction

    def render_no_problem_defined(self, attachments: List[str] = None) -> str:
        """Render the interface when no problem is defined"""
        if attachments is None:
            attachments = []

        attachments_section = self._format_attachments(attachments)

        return f"""# Deep Research Interface

## Introduction

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Please check this section if your commands don't seem to be working as expected.

To begin, you need to define the problem you'll be researching. Please follow these standards and best practices:
- Make the problem statement clear and specific
- Include any constraints or requirements
- Consider what a successful outcome would look like
- Don't expand from the scope of the provided instructions from the user. The smaller the scope of the problem the faster the user will receive the answer.
- Include expectations on the depth of the results. On average be frugal, not making the problems scope explode.

Note: This is a temporary state. After defining the problem, this chat will be discarded and you'll start working on the problem with a fresh interface.

Any attachments provided will be copied to the root problem after creation and won't be lost.

Any context provided to you in the context section will be permanent and accessible in the future while working on the problem, so you can refer to it if needed.

Please note that only one problem definition is allowed. Problem definition is the only action you should take at this point and finish the response message.

Make sure to include closing tags for command blocks, otherwise it will break the parsing and cause syntax errors.

======================
# Attachments

{attachments_section}

======================
# Instruction
{self.instruction}

======================
# How to define a problem
Define the problem using this command:
```
<<< define_problem
///title
title goes here
///content
Content of the problem definition.
>>>
```"""

    def render_problem_defined(self) -> str:
        """Render the interface when a problem is defined"""
        if not self.file_system.current_node:
            return "Error: No current node"

        current_node = self.file_system.current_node

        # Format attachments
        attachments_section = self._format_attachments_from_node(current_node)

        # Format criteria
        criteria_section = self._format_criteria(current_node)

        # Format breakdown structure
        breakdown_section = self._format_breakdown_structure(current_node)

        # Format completed reports
        completed_reports_section = self._format_completed_reports(current_node)

        # Format parent chain
        parent_chain_section = self._format_parent_chain()

        # Format problem hierarchy
        problem_hierarchy = self.file_system.get_problem_hierarchy()

        return f"""# Deep Research Interface

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

{attachments_section}

======================
# Instruction
{self.instruction}

======================
# Current Problem: {current_node.title}

## Problem Hierarchy
{problem_hierarchy}

## Problem Definition
{current_node.problem_definition}

## Criteria of Definition of Done
{criteria_section}

## Breakdown Structure
{breakdown_section}

## Completed Reports
{completed_reports_section}

{parent_chain_section}

## Goal
Your goal is to solve the root problem. Stay frugal, don't focus on the unnecessary details that won't benefit the root problem. If you find yourself working on something that's not worth the effort, mark as done, write it in the report and go up.
Your current focus in the current task as provided above.
Add criteria for the current problem if needed, create subproblems to structure your investigation, and work toward producing a comprehensive 3-page report. Use the attachments for reference and add new ones as needed. When ready to move to a different focus area, use the focus commands.
Remember, we work backwards from the root problem.
"""

    def _format_attachments(self, attachments: List[str]) -> str:
        """Format attachments for display"""
        if not attachments:
            return "<attachments>\nNo attachments available.\n</attachments>"

        result = "<attachments>\n"
        for attachment in attachments:
            result += f'<attachment name="{attachment}">\n'
            result += "Content would be displayed here...\n"
            result += "</attachment>\n"
        result += "</attachments>"
        return result

    def _format_attachments_from_node(self, node: Node) -> str:
        """Format attachments from a node for display"""
        if not node.attachments:
            return "<attachments>\nNo attachments available.\n</attachments>"

        result = "<attachments>\n"
        for name, attachment in node.attachments.items():
            result += f'<attachment name="{name}">\n'
            result += f"{attachment.content}\n"
            result += "</attachment>\n"
        result += "</attachments>"
        return result

    def _format_criteria(self, node: Node) -> str:
        """Format criteria for display"""
        if not node.criteria:
            return "No criteria defined yet."

        result = ""
        for i, (criterion, done) in enumerate(zip(node.criteria, node.criteria_done)):
            status = "[✓]" if done else "[ ]"
            result += f"{i+1}. {status} {criterion}\n"
        return result.strip()

    def _format_breakdown_structure(self, node: Node) -> str:
        """Format breakdown structure for display"""
        if not node.subproblems:
            return "No subproblems defined yet."

        result = ""
        for title, subproblem in node.subproblems.items():
            criteria_status = subproblem.get_criteria_status()
            result += f"### {title} {criteria_status}\n"
            result += f"{subproblem.problem_definition}\n\n"

            # Add criteria for this subproblem if any exist
            if subproblem.criteria:
                result += "#### Criteria:\n"
                for i, (criterion, done) in enumerate(
                    zip(subproblem.criteria, subproblem.criteria_done)
                ):
                    status = "[✓]" if done else "[ ]"
                    result += f"{i+1}. {status} {criterion}\n"
                result += "\n"
        return result.strip()

    def _format_completed_reports(self, node: Node) -> str:
        """Format completed reports for display"""
        result = ""

        # Add child reports section if there are any subproblems with reports
        has_child_reports = any(
            subproblem.report for subproblem in node.subproblems.values()
        )
        if has_child_reports:
            result += "### Child Reports\n"
            for title, subproblem in node.subproblems.items():
                if subproblem.report:
                    result += "<Report>\n"
                    result += f"#### {title}\n"
                    result += f"{subproblem.report}\n\n"
                    result += "<\Report>\n"

        # Add current report if it exists
        if node.report:
            result += "### Current Report\n"
            result += f"{node.report}\n\n"

        return result.strip() if result else "No reports available yet."

    def _format_parent_chain(self) -> str:
        """Format parent chain for display"""
        chain = self.file_system.get_parent_chain()
        if len(chain) <= 1:
            return ""

        result = "## Parent chain\n"

        # Skip the current node
        for i, node in enumerate(chain[:-1]):
            result += (
                f"### L{i} {'Root Problem' if i == 0 else 'Problem'}: {node.title}\n"
            )
            result += f"{node.problem_definition}\n\n"

            if node.subproblems:
                result += f"#### L{i} Problem Breakdown Structure\n"
                for title, subproblem in node.subproblems.items():
                    result += f"##### {title}\n"
                    result += f"{subproblem.problem_definition}\n\n"

        return result.strip()
