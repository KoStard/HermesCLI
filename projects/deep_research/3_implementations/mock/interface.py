from typing import List, Optional

from .file_system import FileSystem, Node


class Interface:
    def __init__(self, file_system: FileSystem, instruction: str):
        self.file_system = file_system
        self.instruction = instruction

    def render_no_problem_defined(self, attachments: List[str] = None) -> str:
        """Render the interface when no problem is defined"""
        if attachments is None:
            attachments = []

        attachments_section = self._format_attachments(attachments)

        return f"""# Deep Research Interface

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Please check this section if your commands don't seem to be working as expected.

To begin, you need to define the problem you'll be researching. Please follow these standards and best practices:
- Make the problem statement clear and specific
- Include any constraints or requirements
- Consider what a successful outcome would look like

Note: This is a temporary state. After defining the problem, this chat will be discarded and you'll start working on the problem with a fresh interface.

Any attachments provided will be copied to the root problem after creation and won't be lost.

Please note that only one problem definition is allowed. Problem definition is the only action you should take at this point and finish the response message.

Make sure to include closing tags for multiline blocks, otherwise it will break the parsing and cause syntax errors.

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
<<<<< define_problem
///title
title goes here
///content
Content of the problem definition.
>>>>>
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
        
        # Format parent chain
        parent_chain_section = self._format_parent_chain()
        
        # Format problem hierarchy
        problem_hierarchy = self.file_system.get_problem_hierarchy()
        
        # Check if we're at the root
        finish_task_command = "- ///finish_task (when all criteria are met and report is written)\n" if current_node == self.file_system.root_node else ""

        return f"""# Deep Research Interface

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems. You can use commands to add criteria, create subproblems, attach resources, write reports, and navigate the problem hierarchy.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

The chat history will be erased with every focus change, as it represents a new beginning with a different problem focus.

Please use commands exactly as shown, with correct syntax. Closing tags are mandatory for multiline blocks, otherwise parsing will break.

Note that only the attachments of the current problem are visible. When changing focus, the available attachments will change as well.

Important: Only one focus change is allowed in one response. The focus change command should be the last command in your message, as it marks the end of the current session. No further commands should follow a focus change.

## Simple Commands
- ///add_criteria Your criteria text here
- ///mark_criteria_as_done criteria_number
- ///focus_down Subproblem Title
- ///focus_up (when done with the subproblem, focus up)
{finish_task_command}
## Block Commands
```
<<<<< add_subproblem
///title
Subproblem Title
///content
Problem definition goes here
>>>>>
```

```
<<<<< add_attachment
///name
attachment_name.txt
///content
Content goes here
>>>>>
```

```
<<<<< write_report
///content
Report content goes here
>>>>>
```

```
<<<<< append_to_problem_definition
///content
Content to append to the problem definition.
>>>>>
```
This might be needed if the direction needs to be adjusted based on user input.

```
<<<<< add_criteria_to_subproblem
///title
Subproblem Title
///criteria
Your criteria text here (should be a single line)
>>>>>
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

{parent_chain_section}

## Goal
Your task is to continue investigating the current problem on {current_node.title}. Add criteria if needed, create subproblems to structure your investigation, and work toward producing a comprehensive 3-page report. Use the attachments for reference and add new ones as needed. When ready to move to a different focus area, use the focus commands."""

    def _format_attachments(self, attachments: List[str]) -> str:
        """Format attachments for display"""
        if not attachments:
            return "<attachments>\nNo attachments available.\n</attachments>"
        
        result = "<attachments>\n"
        for attachment in attachments:
            result += f"<attachment name=\"{attachment}\">\n"
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
            result += f"<attachment name=\"{name}\">\n"
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
                for i, (criterion, done) in enumerate(zip(subproblem.criteria, subproblem.criteria_done)):
                    status = "[✓]" if done else "[ ]"
                    result += f"{i+1}. {status} {criterion}\n"
                result += "\n"
        return result.strip()

    def _format_parent_chain(self) -> str:
        """Format parent chain for display"""
        chain = self.file_system.get_parent_chain()
        if len(chain) <= 1:
            return ""
        
        result = "## Parent chain\n"
        
        # Skip the current node
        for i, node in enumerate(chain[:-1]):
            result += f"### L{i} {'Root Problem' if i == 0 else 'Problem'}: {node.title}\n"
            result += f"{node.problem_definition}\n\n"
            
            if node.subproblems:
                result += f"#### L{i} Problem Breakdown Structure\n"
                for title, subproblem in node.subproblems.items():
                    result += f"##### {title}\n"
                    result += f"{subproblem.problem_definition}\n\n"
        
        return result.strip()
