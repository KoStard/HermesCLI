from typing import List, Optional

from .file_system import Artifact, FileSystem, Node


class DeepResearcherInterface:
    def __init__(self, file_system: FileSystem, instruction: str):
        self.file_system = file_system
        self.instruction = instruction

    def render_no_problem_defined(self, artifacts: List[str] = None) -> str:
        """Render the interface when no problem is defined"""
        if artifacts is None:
            artifacts = []

        artifacts_section = self._format_artifacts(artifacts)

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

Any artifacts provided will be copied to the root problem after creation and won't be lost. Once the problem is defined, you'll be able to see artifacts from the current problem, all its parent problems, and all descendant problems.

Any context provided to you in the context section will be permanent and accessible in the future while working on the problem, so you can refer to it if needed.

Please note that only one problem definition is allowed. Problem definition is the only action you should take at this point and finish the response message.

Make sure to include closing tags for command blocks, otherwise it will break the parsing and cause syntax errors.

======================
# Artifacts (Initial)

{artifacts_section}

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

    def render_problem_defined(self, target_node, permannet_logs) -> str:
        """Render the interface when a problem is defined"""
        # Format artifacts from current node, parent chain, and all descendants
        artifacts_section = self._format_all_artifacts(target_node)

        # Format criteria
        criteria_section = self._format_criteria(target_node)

        # Format breakdown structure
        breakdown_section = self._format_breakdown_structure(target_node)

        # Format permanent log
        permanent_log_section = self._format_permanent_log(permannet_logs)

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

### Problem Status System

Each problem in the hierarchy has a status that indicates its current state:
- **NOT_STARTED**: A problem that has been created but work has not yet begun on it
- **PENDING**: A problem that is temporarily paused because focus has moved to one of its subproblems
- **CURRENT**: The problem you are currently focused on and working to solve
- **FINISHED**: A problem that has been successfully completed
- **FAILED**: A problem that could not be solved or was determined to be unsolvable
- **CANCELLED**: A problem that was determined to be unnecessary or irrelevant

You can see the status of each problem in the breakdown structure. The current problem is always marked as CURRENT.

### Artifacts

Artifacts are your primary way to create value while working on problems. They represent the concrete outputs of your research and analysis. Whenever you find important information that moves the root problem towards a solution, capture it in the form of an artifact. High-quality artifacts are the main deliverable of your work.

You'll see artifacts from the current problem, all parent problems, and all descendant problems. This gives you a complete view of all the valuable outputs created throughout the problem hierarchy.

### Log Management

The `add_log_entry` command allows you to log permanent, one-sentence summaries of key actions or milestones in the Permanent Logs section. Its purpose is to maintain a clear, concise record of progress across focus changes, ensuring you don't lose track of what's been done when the chat history resets. This is crucial because it helps you stay aligned with the root problem's goals, avoids redundant work, and provides context for reports or navigation (e.g., confirming all subtasks are finished before focusing up). Use it whenever you take actions - like creating a subtask, adding an artifact, or finishing a problem - to document outcomes that matter to the hierarchy. Add entries right after the action, keeping them specific and brief (e.g., "Subtask 1 artifact created" rather than "Did something"). This keeps the history actionable and relevant.
Make sure to include `add_log_entry` for every single focus change you make. Add this before making the focus change.

======================
# Permanent Logs
{permanent_log_section}


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

; if a subproblem is no longer necessary or relevant, you can cancel it
<<< cancel_subproblem
///title
Subproblem Title
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

<<< add_artifact
///name
artifact_name.md
///content
Content goes here
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

<<< add_log_entry
///content
One-sentence summary of a key action or milestone.
>>>
```

======================
# Artifacts (Current Problem, Parent Chain & Descendants)

{artifacts_section}

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


{parent_chain_section}

## Goal
Your goal is to solve the root problem. Stay frugal, don't focus on the unnecessary details that won't benefit the root problem. If you find yourself working on something that's not worth the effort, mark as done, write it in the report and go up.
Your current focus in the current problem as provided above.
Add criteria for the current problem if needed, create subproblems to structure your investigation, and work toward producing a comprehensive 3-page report. Use the attachments for reference and add new ones as needed. When ready to move to a different focus area, use the focus commands.
Remember, we work backwards from the root problem.
"""

    def _format_artifacts(self, artifacts: List[str]) -> str:
        """Format artifacts for display"""
        if not artifacts:
            return "<artifacts>\nNo artifacts available.\n</artifacts>"

        result = "<artifacts>\n"
        for artifact in artifacts:
            result += f'<artifact name="{artifact}">\n'
            result += "Content would be displayed here...\n"
            result += "</artifact>\n"
        result += "</artifacts>"
        return result

    def _format_all_artifacts(self, node: Node) -> str:
        """Format artifacts from a node, its parent chain, and all descendants for display"""
        if not node:
            return "<artifacts>\nNo artifacts available.\n</artifacts>"
            
        # Get all nodes in the parent chain, including current node
        parent_chain = self.file_system.get_parent_chain(node)
        
        # Collect all artifacts with their owner information
        all_artifacts = []
        
        # Add artifacts from parent chain
        for parent_node in parent_chain:
            for name, artifact in parent_node.artifacts.items():
                all_artifacts.append((name, artifact, parent_node.title, "parent"))
        
        # Add artifacts from all descendants
        descendant_artifacts = self.collect_artifacts_recursively(node)
        for owner_title, name, content in descendant_artifacts:
            # Skip artifacts from the current node as they're already included in the parent chain
            if owner_title != node.title:
                all_artifacts.append((name, Artifact(name=name, content=content), owner_title, "descendant"))
        
        if not all_artifacts:
            return "<artifacts>\nNo artifacts available.\n</artifacts>"

        result = "<artifacts>\n"
        for name, artifact, owner, relationship in all_artifacts:
            result += f'<artifact name="{name}">\n'
            result += f"---\n"
            result += f"owner: {owner} ({relationship})\n"
            result += f"---\n\n"
            result += f"{artifact.content}\n"
            result += "</artifact>\n"
        result += "</artifacts>"
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
            status_label = subproblem.get_status_label()
            result += f"### {title} {criteria_status} [Status: {status_label}]\n"
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

    def collect_artifacts_recursively(self, node: Node) -> list:
        """Recursively collect artifacts from a node and all its descendants"""
        artifacts = []
        
        # Add this node's artifacts
        for name, artifact in node.artifacts.items():
            artifacts.append((node.title, name, artifact.content))
            
        # Recursively collect artifacts from all subproblems
        for title, subproblem in node.subproblems.items():
            artifacts.extend(self.collect_artifacts_recursively(subproblem))
            
        return artifacts


    def _format_permanent_log(self, permannet_logs: list) -> str:
        """Format permanent history for display"""
        if not permannet_logs:
            return "<permanent_log>\nNo history entries yet.\n</permanent_log>"
            
        entries = "\n".join(f"- {entry}" for entry in permannet_logs)
        return f"<permanent_log>\n{entries}\n</permanent_log>"

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
