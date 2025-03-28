from typing import List, Tuple

from .command import CommandRegistry
from .file_system import FileSystem, Node, Artifact
from .commands import DefineCommand  # registers the commands
from .hierarchy_formatter import HierarchyFormatter


class DeepResearcherInterface:
    """
    Responsible for rendering interface content as strings.
    This class handles all string formatting and presentation logic.
    """

    def __init__(self, file_system: FileSystem, instruction: str):
        self.file_system = file_system
        self.instruction = instruction
        self.hierarchy_formatter = HierarchyFormatter()

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
Notice: The assistants working on the created problem won't see anymore this instruction. Make sure to include all the important details in the problem definition.

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
        subproblems_sections = self._format_subproblems(target_node)
        
        # Format permanent log
        permanent_log_section = self._format_permanent_log(permanent_logs)

        # Format problem path hierarchy
        problem_path_hierarchy_section = self._format_problem_path_hierarchy(target_node)

        # Format problem hierarchy - full tree with current node highlighted
        problem_hierarchy = self.file_system.get_problem_hierarchy(target_node)
        
        command_help = self._generate_command_help()
        
        # Check if the current node is too deep and add a warning if needed
#
        depth_warning = ""
        if self.file_system.is_node_too_deep(target_node, 3):
            depth_warning = f"""
⚠️ **DEPTH WARNING** ⚠️
You are currently at depth level {target_node.depth_from_root}, which exceeds the recommended maximum of 3 levels.
Please avoid creating additional subproblems at this level. Instead:
1. Try to solve the current problem directly
2. Use `finish_problem` to allow the parent problem to resume
3. If necessary, mark the current problem as failed using `fail_problem` command

Excessive depth makes the problem hierarchy difficult to manage and can lead to scope creep.
"""

        static_content = f"""# Deep Research Interface (Static Section)

## Introduction

### Mission

You, as well as your team, are working on the provided problems.
Each of you have a version of this device in front of you.
It's a special interface allowing you to do many things that are necessary to finish the task.

### About the workforce

You are part of a dynamically sized team of professionals focused on gradual iterative research fitting in the budget.
You are not working on this problem alone.
The team receives one "root problem", which is like the EPIC you want to resolve.
Someone from the team (maybe you) picks up the root problem. Others will get subproblems. The principle is the same:
1. Start your research of the problem.
2. Rely on your existing significant knowledge of the domain.
3. If necessary, use the provided commands to **request** more information/knowledge (then **stop** to receive them)
4. If the problem is still too vague/big to solve alone, break it into subproblems that your teammates will handle. You'll see the artifacts they create for the problems, and the sub-subproblems they create. When you active another problem, you should **stop** to let them continue.
5. Then based on the results of the subproblems, continue the investigation (going back to step 2), creating further subproblems if necessary, or resolving the current problem.

All of you are pragmatic, yet have strong ownership. You make sure you solve as much of the problem as possible, while also delegating (which is a good sign of leadership) tasks to your teammates as well.

### Using the interface

This interface helps you conduct thorough research by providing you with the necessary tools and to create subtasks with less vague scope that your teammates will do. You can use commands to add criteria, create subproblems, attach resources, write reports, navigate the problem hierarchy, access external resources, and more.

In case the interface has a bug and you are not able to navigate, you can use an escape code "SHUT_DOWN_DEEP_RESEARCHER". If the system detects this code anywhere in your response it will halt the system and the admin will check it.

You see a keyboard and a screen. It's a text-only chat-like interface. You write a full message, send it, then see some actions happen based on the commands that you used. While you are writing, nothing happens.

Your immediate goal is to write the message that will be sent to the engine. Everything you write is included in the message. Then you finish the message, it's processed and you receive a response.

If you need more information, you reply with a partial message, using commands to receive more response.

If you need to create subproblems and activate them, you reply with a partial message, to activate and wait for them.

If you are working on a big problem and want to solve it piece by piece, reply with partial messages as many times as you want.
Only after you have completely finished the task, you resolve the current problem. Reminder that the commands from the current message will be executed only after you finish it. So it's a good practice to not have regular commands (information gathering, criteria change, etc) in the same message as problem resolution (finish or fail) or subproblem activation.
You need to send the whole message which contains the commands you want to be executed to receive responses.

### Subproblems

Include expectations on the depth of the results in problem definitions. On average be frugal, not making the problems scope explode.
Only one teammate will be working on one (sub)problem. The history of the work will not be shared, except for the artifacts, problem hierarchy and shared permanent logs.

### Depth

Depth is how far we are from the root problem.
Root problem has a depth of 0.
Subproblems of the root problem has a depth of 1. Etc.
As a rule of thumn, unless really necessary, don't go below depth 3.

### Problem Status System

Each problem in the hierarchy has a status that indicates its current state:
- **NOT_STARTED**: A problem that has been created but work has not yet begun on it
- **PENDING**: A problem that is temporarily paused because it awaits the results of its subproblems
- **IN_PROGRESS**: The problem that is being currently worked on
- **FINISHED**: A problem that has been successfully completed
- **FAILED**: A problem that could not be solved or was determined to be unsolvable
- **CANCELLED**: A problem that was determined to be unnecessary or irrelevant

You can see the status of each problem in the breakdown structure.

### Artifacts

Artifacts are your primary way to create value while working on problems. They represent the concrete outputs of your research and analysis. Whenever you find important information that moves the root problem towards a solution, capture it in the form of an artifact. High-quality artifacts are the main deliverable of your work.
All of your artifacts should rely on your factual knowledge or specific resources you have access to or get through commands usage. Include source links/commands. In artifacts, factuality is essential, and assumptions are not allowed. If you lack information, clearly call out that you don't have that knowledge, what tools are missing and how will you proceed forward. We have culture of growth, so clear call out of missing knowledge is considered sign of maturity.

You'll see partially open artifacts from all problems in the system, that you have option to open fully for yourself. This gives you a complete view of all the valuable outputs created throughout the problem hierarchy.

The outputs of the commands are temporary and won't be visible from other nodes. Include all factual details in the artifacts.

No need to copy the artifacts between problems or into the root problem.
As artifacts are written as markdown files, you can refer to the child artifacts with markdown links. The artifacts are located in "Artifacts" folder in the child path (which consists of a directory with the child problem's title as name).
Example:
> [Child artifact](Subproblem Title/Sub-subproblem Title/Artifacts/Child Artifact.md) 

### Log Management

The `add_log_entry` command allows you to log permanent, one-sentence summaries of key actions or milestones in the Permanent Logs section. Its purpose is to maintain a clear, concise record of progress across all problems, ensuring the overall progress is always visible. This is crucial because it helps you stay aligned with the root problem's goals, avoids redundant work, and provides context for reports or navigation. Use it whenever you take actions - like creating a subtask, adding an artifact, or finishing a problem - to document outcomes that matter to the hierarchy. Add entries right after the action, keeping them specific and brief (e.g., "Artifact 1 artifact created in task with title ..." rather than "Did something"). This keeps the history actionable and relevant.

## Planning

When you receive the request, you should decide from beginning what you want to reply with.
- If you have all the information from beginning and are confident about it, reply with a command to creat artifacts and finish/fail the problem. This is called a final response.
- If you have all the information needed (no other commands to be sent) and you want to define subproblems, do it without other commands (except maybe logs)
- If you lack information, reply with the provided commands and send your message to receive the outputs as automatic response. This is called a partial response. If there are multiple sources you want to check, combine them into one message.

## Commands

If there are any errors with your commands, they will be reported in the "Errors report" section of the automatic reply. Command execution failures will be shown in the "Execution Status Report" section. Please check these sections if your commands don't seem to be working as expected.

Use commands exactly as shown, with correct syntax. Closing tags are mandatory, otherwise parsing will break. The commands should start from an empty line, from first symbol in the line. Don't put anything else in the lines of the commands.

You write down the commands you want to send in this interface. If you activate another problem, you won't see the outputs of other commands you send. You should hence send multiple small messages instead.

Example:
```
❌ Wrong:
search + create artifacts + activate_subproblem (all in one message)

✅ Right:
Message 1: search command
[wait for results]
SYSTEM RESPONSE: results...
Message 2: create artifacts based on search results
[wait for confirmation]
SYSTEM RESPONSE: results...
Message 3: activate_subproblem
SYSTEM RESPONSE: results...
```
⚠️ **IMPORTANT**: Commands are processed AFTER you send your message. Finish your message, read the responses, then consider the next steps.

Notice that we use <<< for opening the commands, >>> for closing, and /// for arguments. Make sure you use the exact syntax.

{command_help}

### Commands troubleshooting

#### 1. No results

If you send a command, a search, and don't see any results, that's likely because you didn't finish your message to wait for the engine to process the whole message. Just finish your message and wait.

## The problem assigned to you

Notice that the problem assigned to you doesn't change during the whole chat.

Title: "{target_node.title}"
{depth_warning}

### Problem Definition
{target_node.problem_definition}

"""
        dynamic_content = f"""
# Deep Research Interface (Dynamic Section)
Here goes the dynamic section of the interface. This is a special section which is visible only in the last message you see.
The interface will be automatically refreshed with every message and you'll see the most up to date information. This is your source of truth for the changing information. The interface will be in the last message you receive and to be frugal with the length of the history and to prevent confusion, will be redacted from the previous messages.

======================
# Permanent Logs
{permanent_log_section}

======================
# Artifacts (All Problems)

{artifacts_section}

======================
## Problem Hierarchy (short)
Notice: The problem hierarchy includes all the problems in the system and their hierarchical relationship, with some metadata. 
The current problem is marked with isCurrent="true".

{problem_hierarchy}

## Criteria of Definition of Done
{criteria_section}

## Subproblems of the current problem
{subproblems_sections}

## Problem Path Hierarchy (from root to current)
{problem_path_hierarchy_section}

## Goal
Your fundamental goal is to solve the root problem through solving the your assigned problem. Stay frugal, don't focus on the unnecessary details that won't benefit the root problem. But don't sacrifice on quality. If you find yourself working on something that's not worth the effort, mark as done and write it in the report.
Remember, we work backwards from the root problem.

# So, what's your message to the engine?
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

    def _format_subproblems(self, node: Node) -> str:
        """Format breakdown structure for display"""
        return self.hierarchy_formatter.format_subproblems(node)

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

    def _format_problem_path_hierarchy(self, node: Node) -> str:
        """Format the hierarchical path from root to current node for display"""
        return self.hierarchy_formatter.format_problem_path_hierarchy(node)

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
