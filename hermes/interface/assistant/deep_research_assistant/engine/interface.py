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
- Explicitely describe what should the answer have to be considered as done.
- For broad topics, provide guidance on how to bring the scope down.

Note: This is a temporary state. After defining the problem, this chat will be discarded and you'll start working on the problem with a fresh interface.

Any attachments provided will be copied to the root problem after creation and won't be lost. Once the problem is defined, you'll be able to see attachments from the current problem and all its parent problems.

Any context provided to you in the context section will be permanent and accessible in the future while working on the problem, so you can refer to it if needed.

Please note that only one problem definition is allowed. Problem definition is the only action you should take at this point and finish the response message.

Make sure to include closing tags for command blocks, otherwise it will break the parsing and cause syntax errors.

======================
# Attachments (Initial)

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

    def render_problem_defined(self, target_node=None) -> str:
        """Render the interface when a problem is defined"""
        # Format attachments
        attachments_section = self._format_attachments_from_node(target_node)

        # Format criteria
        criteria_section = self._format_criteria(target_node)

        # Format breakdown structure
        breakdown_section = self._format_breakdown_structure(target_node)

        # Format completed reports
        completed_reports_section = self._format_completed_reports(target_node)

        # Format parent chain
        parent_chain_section = self._format_parent_chain(target_node)

        # Format problem hierarchy
        problem_hierarchy = self.file_system.get_problem_hierarchy(target_node)

        return f"""# Deep Research Interface

## Introduction

### Using the interface

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems. You can use commands to add criteria, create subproblems, attach resources, write reports, and navigate the problem hierarchy.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

Please use commands exactly as shown, with correct syntax. Closing tags are mandatory for multiline blocks, otherwise parsing will break. The commands should start from an empty line, from first symbol in the line. Don't put anything else in the lines of the commands.

In case the interface has a bug and you are not able to navigate, you can use an escape code "SHUT_DOWN_DEEP_RESEARCHER". If the system detects this code anywhere in your response it will halt the system.

### Hierarchy

Your project is solving the root problem (created or updated by the user instructions which are also accessible to you). If the root problem is too big, you create subproblems and solve them before solving the root problem. Recursively you go deeper until you reach to problems that you can confidently solve directly without need for subproblems. Hence the hierarchy of parent/child problems. Don't create subproblems in cases where you confidently can't answer. Create the minimum number of subproblems necessary to solve the current problem.

Include expectations on the depth of the results in problem definitions. On average be frugal, not making the problems scope explode.

The chat history will be erased with every focus change, as it represents a new beginning with a different problem focus.

Note that attachments from both the current problem and all parent problems are visible. Each attachment shows its owner (the problem it belongs to) at the top. When changing focus, new attachments from that problem will become available.

At most only one focus change is allowed in one response. The focus change command should be the last command in your message, as it marks the end of the current session. No further commands should follow a focus change.

You should go maximum 3 levels deep.

### Attachments

Attachments are your way to capture and collect learnings while you are working on problems. Whenever you find important information that is moving the root problem towards solution, capture in the form of attachment. It will also help the subproblems to have more context to work better. You see the attachments of the current problem and all the problems in the parent chain.

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

; when executed on a subproblem, focus up to its parent problem
; when executed on the root problem, will finish the whole task (i.e. will move the status from "In Progress" to "Completed")
<<< focus_up
>>>

; if for some reason the current problem can't be resolved at all, and you want to mark it as failed, use this. Preferrably include some information in the report before moving up, so that the parent session will have information on why.
<<< fail_problem_and_focus_up
>>>

<<< add_subproblem
///title
Subproblem Title
///content
Problem definition goes here.
Explicitely state why is this essential for the root problem. How does it contribute to the root problem? If it's not, don't create the subproblem!
If we estimate the value we get from this problem in the context of the root problem compared to the effort needed to solve this subproblem, we should have ±20% effort for ±80% value. If we don't have it, don't create the subproblem.

- Make the problem statement clear and specific
- Include any constraints or requirements
- Consider what a successful outcome would look like
- Don't expand from the scope of the provided instructions from the user. The smaller the scope of the problem the faster the user will receive the answer.
- Include expectations on the depth of the results. On average be frugal, not making the problems scope explode.
- Explicitely describe what should the answer have to be considered as done.
- For broad topics, provide guidance on how to bring the scope down.
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
# Attachments (Current Problem & Parent Chain)

{attachments_section}

======================
# Instruction
{self.instruction}

======================
# Current Problem: {target_node.title}

## Problem Hierarchy
{problem_hierarchy}

## Problem Definition
{target_node.problem_definition}

## Criteria of Definition of Done
{criteria_section}

## Breakdown Structure
{breakdown_section}

## Completed Reports
{completed_reports_section}

{parent_chain_section}

## Goal
Your goal is to solve the root problem. Stay frugal, don't focus on the unnecessary details that won't benefit the root problem. If you find yourself working on something that's not worth the effort, mark as done, write it in the report and go up.
Your current focus in the current problem as provided above.
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
        """Format attachments from a node and its parent chain for display"""
        if not node:
            return "<attachments>\nNo attachments available.\n</attachments>"
            
        # Get all nodes in the parent chain, including current node
        parent_chain = self.file_system.get_parent_chain(node)
        
        # Collect all attachments with their owner information
        all_attachments = []
        for parent_node in parent_chain:
            for name, attachment in parent_node.attachments.items():
                all_attachments.append((name, attachment, parent_node.title))
        
        if not all_attachments:
            return "<attachments>\nNo attachments available.\n</attachments>"

        result = "<attachments>\n"
        for name, attachment, owner in all_attachments:
            result += f'<attachment name="{name}">\n'
            result += f"---\n"
            result += f"owner: {owner}\n"
            result += f"---\n\n"
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

    def _collect_reports_recursively(self, node: Node) -> list:
        """Recursively collect reports from a node and all its descendants"""
        reports = []
        
        # Add this node's report if it exists
        if node.report:
            reports.append((node.title, node.report))
            
        # Recursively collect reports from all subproblems
        for title, subproblem in node.subproblems.items():
            reports.extend(self._collect_reports_recursively(subproblem))
            
        return reports

    def _format_completed_reports(self, node: Node) -> str:
        """Format completed reports for display"""
        result = ""

        # Add current report if it exists
        if node.report:
            result += "### Current Report\n"
            result += f"{node.report}\n\n"

        # Collect all descendant reports recursively
        all_descendant_reports = []
        for title, subproblem in node.subproblems.items():
            all_descendant_reports.extend(self._collect_reports_recursively(subproblem))
            
        # Add descendant reports section if there are any
        if all_descendant_reports:
            result += "### Descendant Reports\n"
            for owner_title, report in all_descendant_reports:
                result += "<Report>\n"
                result += f"---\n"
                result += f"owner: {owner_title}\n"
                result += f"---\n\n"
                result += f"{report}\n\n"
                result += "</Report>\n"

        return result.strip() if result else "No reports available yet."

    def _format_parent_chain(self, node: Node) -> str:
        """Format parent chain for display"""
        if not node:
            return ""
            
        chain = self.file_system.get_parent_chain(node)
        if len(chain) <= 1:
            return ""

        result = "## Parent chain\n"

        # Skip the current node
        for i, parent_node in enumerate(chain[:-1]):
            result += (
                f"### L{i} {'Root Problem' if i == 0 else 'Problem'}: {parent_node.title}\n"
            )
            result += f"{parent_node.problem_definition}\n\n"

            if parent_node.subproblems:
                result += f"#### L{i} Problem Breakdown Structure\n"
                for title, subproblem in parent_node.subproblems.items():
                    result += f"##### {title}\n"
                    result += f"{subproblem.problem_definition}\n\n"

        return result.strip()
