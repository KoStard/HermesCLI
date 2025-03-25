from typing import List, Tuple

from .command import CommandRegistry
from .file_system import FileSystem, Node, Artifact
from .commands import DefineCommand  # registers the commands


class DeepResearcherInterface:
    """
    Responsible for rendering interface content as strings.
    This class handles all string formatting and presentation logic.
    """

    def __init__(self, file_system: FileSystem, instruction: str):
        self.file_system = file_system
        self.instruction = instruction

    def render_no_problem_defined(self) -> Tuple[str, str]:
        """Render the interface when no problem is defined"""

        static_content = f"""# Deep Research Interface

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
        return static_content, ""

    def render_problem_defined(self, target_node: Node, permanent_logs: List[str]) -> Tuple[str, str]:
        """Render the interface when a problem is defined"""
        # Format artifacts from current node, parent chain, and all descendants
        artifacts_section = self._format_all_artifacts(target_node)

        # Format criteria
        criteria_section = self._format_criteria(target_node)

        # Format breakdown structure with status information
        breakdown_section = self._format_breakdown_structure(target_node)
        
        # Format permanent log
        permanent_log_section = self._format_permanent_log(permanent_logs)

        # Format parent chain
        parent_chain_section = self._format_parent_chain(target_node)

        # Format problem hierarchy - full tree with current node highlighted
        problem_hierarchy = self.file_system.get_problem_hierarchy(target_node)
        
        command_help = self._generate_command_help()
        
        # Check if the current node is too deep and add a warning if needed
#
        depth_warning = ""
        if self.file_system.is_node_too_deep(target_node, 3):
            depth_warning = """
⚠️ **DEPTH WARNING** ⚠️
You are currently at depth level {depth}, which exceeds the recommended maximum of 3 levels.
Please avoid creating additional subproblems at this level. Instead:
1. Try to solve the current problem directly
2. Use 'focus_up' to return to the parent problem when done
3. If necessary, mark the problem as done or failed using 'fail_problem_and_focus_up'

Excessive depth makes the problem hierarchy difficult to manage and can lead to scope creep.
""".format(depth=target_node.depth_from_root)

        static_content = f"""# Deep Research Interface (Static Section)
## Introduction

### Using the interface

This interface helps you conduct thorough research by breaking down complex problems into manageable subproblems. You can use commands to add criteria, create subproblems, attach resources, write reports, and navigate the problem hierarchy.

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

Please use commands exactly as shown, with correct syntax. Closing tags are mandatory for multiline blocks, otherwise parsing will break. The commands should start from an empty line, from first symbol in the line. Don't put anything else in the lines of the commands.

In case the interface has a bug and you are not able to navigate, you can use an escape code "SHUT_DOWN_DEEP_RESEARCHER". If the system detects this code anywhere in your response it will halt the system.

### Hierarchy

Your project is solving the root problem (created or updated by the user instructions which are also accessible to you). If the root problem is too big, you create subproblems and solve them before solving the root problem. Recursively you go deeper until you reach to problems that you can confidently solve directly without need for subproblems. Hence the hierarchy of parent/child problems. Don't create subproblems in cases where you confidently can't answer. Create the minimum number of subproblems necessary to solve the current problem.

Include expectations on the depth of the results in problem definitions. On average be frugal, not making the problems scope explode.

The chat history is preserved for each problem node. When you return to a problem you've worked on before, you'll see the previous conversation history for that specific problem. This helps maintain context and continuity as you navigate through the problem hierarchy.

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
All of your artifacts should rely on your factual knowledge or specific resources you have access to or get through commands usage. In deep research artifacts, factuality is essential, and assumptions are not allowed. If you lack information, clearly call out that you don't have that knowledge, what tools are missing and how will you proceed forward.

You'll see artifacts from all problems in the system. This gives you a complete view of all the valuable outputs created throughout the problem hierarchy.

The outputs of the commands are temporary and won't be visible from other nodes. Include all factual details in the artifacts.

No need to copy the artifacts into the root problem from child problems.
You can refer to the child artifacts with markdown links. The artifacts are located in "Artifacts" folder in the child path.
Example:
> [Child artifact](Subproblem Title/Sub-subproblem Title/Artifacts/Child Artifact.md) 

### Log Management

The `add_log_entry` command allows you to log permanent, one-sentence summaries of key actions or milestones in the Permanent Logs section. Its purpose is to maintain a clear, concise record of progress across focus changes, ensuring you don't lose track of what's been done when the chat history resets. This is crucial because it helps you stay aligned with the root problem's goals, avoids redundant work, and provides context for reports or navigation (e.g., confirming all subtasks are finished before focusing up). Use it whenever you take actions - like creating a subtask, adding an artifact, or finishing a problem - to document outcomes that matter to the hierarchy. Add entries right after the action, keeping them specific and brief (e.g., "Subtask 1 artifact created" rather than "Did something"). This keeps the history actionable and relevant.
Make sure to include `add_log_entry` for every single focus change you make. Add this before making the focus change.

## Commands

Commands are executed only after you finish your message. If you want to use the outputs of the command, you should not change focus in that message, you should wait to receive the results after you finish your message, then in the next message take the next steps.

Notice that we use <<< for opening the commands, >>> for closing, and /// for arguments. Make sure you use the exact syntax.

{command_help}
"""
        dynamic_content = f"""
# Deep Research Interface (Dynamic Section)
Here goes the dynamic section of the interface. This is a special section which is visible only in the last message you see.
The interface will be automatically refreshed with every message and you'll see the most up to date information. This is your source of truth. The interface will be in the last message you receive and to be frugal with the length of the history and to prevent confusion, will be redacted from the previous messages.

======================
# Permanent Logs
{permanent_log_section}

======================
# Artifacts (All Problems)

{artifacts_section}

======================
# Root Problem Instruction
Notice: The actions from the instruction are for the root problem. At the level of the current problem you might be 
treating only a piece of it.

{self.instruction}

======================
# Current Problem in Focus: Title "{target_node.title}"
{depth_warning}
## Problem Hierarchy
Notice: The problem hierarchy includes all the problems in the system and their hierarchical relationship, with some metadata. 
The current problem is marked with isCurrent="true".

{problem_hierarchy}

## Problem Definition
{target_node.problem_definition}

## Criteria of Definition of Done
{criteria_section}

## Breakdown of current problem
{breakdown_section}

## Chain of problems from current to root
{parent_chain_section}

## Goal
Your goal is to solve the root problem. Stay frugal, don't focus on the unnecessary details that won't benefit the root problem. But don't sacrifice on quality. If you find yourself working on something that's not worth the effort, mark as done, write it in the report and go up.
Your current focus in the current problem as provided above.
Add criteria for the current problem if needed, create subproblems to structure your investigation, and work toward producing a comprehensive 3-page report. Use the attachments for reference and add new ones as needed. When ready to move to a different focus area, use the focus commands.
Remember, we work backwards from the root problem.
"""
        return static_content, dynamic_content

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
        """Format artifacts from all nodes in the file system"""
        if not node:
            return "<artifacts>\nNo artifacts available.\n</artifacts>"

        # Collect all artifacts with their owner information
        all_artifacts = []

        # Get the root node
        root_node = self.file_system.root_node

        # Collect all artifacts from all nodes in the file system
        all_nodes_artifacts = self.collect_all_artifacts(root_node)
        for owner_title, name, content, is_fully_visible in all_nodes_artifacts:
            all_artifacts.append(
                (
                    name,
                    Artifact(
                        name=name, content=content, is_fully_visible=is_fully_visible
                    ),
                    owner_title,
                    "system",
                )
            )

        if not all_artifacts:
            return "<artifacts>\nNo artifacts available.\n</artifacts>"

        result = "<artifacts>\n"
        for name, artifact, owner, relationship in all_artifacts:
            result += f'<artifact name="{name}">\n'
            result += f"---\n"
            result += f"owner: {owner} ({relationship})\n"
            result += f"---\n\n"

            # Show full content or just first 10 lines based on visibility flag
            if artifact.is_fully_visible:
                result += f"{artifact.content}\n"
            else:
                # Split content into lines and take first 10
                content_lines = artifact.content.split("\n")
                preview_lines = content_lines[:10]
                remaining_count = len(content_lines) - 10

                # Add preview lines
                result += "\n".join(preview_lines)

                # Add message about hidden content if there are more lines
                if remaining_count > 0:
                    result += f"\n\n[...{remaining_count} more lines hidden. Use 'open_artifact' command to view full content...]\n"

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
            status_emoji = subproblem.get_status_emoji()
            
            # Include emoji and more visible status information
            result += f"### {status_emoji} {title} {criteria_status} [Status: {status_label}]\n"
            result += f"{subproblem.problem_definition}\n\n"

            # Add criteria for this subproblem if any exist
            if subproblem.criteria:
                result += "#### Sub-problem's Criteria:\n"
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
            artifacts.append(
                (node.title, name, artifact.content, artifact.is_fully_visible)
            )

        # Recursively collect artifacts from all subproblems
        for title, subproblem in node.subproblems.items():
            artifacts.extend(self.collect_artifacts_recursively(subproblem))

        return artifacts

    def collect_all_artifacts(self, node: Node) -> list:
        """Collect all artifacts from all nodes in the file system"""
        if not node:
            return []

        # Start with artifacts from this node and its descendants
        artifacts = self.collect_artifacts_recursively(node)

        return artifacts

    def _format_permanent_log(self, permanent_logs: list) -> str:
        """Format permanent history for display"""
        if not permanent_logs:
            return "<permanent_log>\nNo history entries yet.\n</permanent_log>"

        entries = "\n".join(f"- {entry}" for entry in permanent_logs)
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
            result += f"### L{i} {'Root Problem' if i == 0 else 'Problem'}: {parent_node.title}\n"
            result += f"{parent_node.problem_definition}\n\n"

            if parent_node.subproblems:
                result += f"#### L{i} Problem Breakdown Structure\n"
                for title, subproblem in parent_node.subproblems.items():
                    result += f"##### {title}\n"
                    result += f"{subproblem.problem_definition}\n\n"

        return result.strip()

    def _generate_command_help(self) -> str:
        """Generate help text for all registered commands"""
        # Get all registered commands
        commands = CommandRegistry().get_problem_defined_interface_commands()

        # Generate command help text
        result = []
        for name, cmd in sorted(commands.items()):
            # Command header with name
            command_text = f"<<< {name}"

            # Add sections
            for section in cmd.sections:
                command_text += f"\n///{section.name}"
                if section.help_text:
                    command_text += f"\n{section.help_text}"
                else:
                    command_text += f"\nYour {section.name} here"

            # Command footer
            command_text += "\n>>>"

            # Add help text if available
            if cmd.help_text:
                command_text += '\n' + '\n'.join('; ' + line for line in cmd.help_text.split('\n'))

            result.append(command_text)

        return "\n\n".join(result)
