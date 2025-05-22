import textwrap
from typing import Any

from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.criteria_manager import Criterion
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.research.research_project_component.knowledge_base import KnowledgeEntry

# Import the new generic base command and registry
from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.commands.command import CommandRegistry

# Import the specific context for Deep Research
from .command_context import CommandContextImpl


class AddCriteriaCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "add_criteria",
            "Add criteria for the current problem",
        )
        self.add_section("criteria", True, "Criteria text")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Add criteria to the current problem"""
        current_node = context.current_node

        # Check if criteria already exists
        criteria_text = args["criteria"]
        existing_criteria = [c.content for c in current_node.get_criteria()]
        if criteria_text in existing_criteria:
            return

        # Create and add a new criterion
        criterion = Criterion(content=criteria_text)
        current_node.add_criterion(criterion)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Criteria '{criteria_text}' added.")


class MarkCriteriaAsDoneCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "mark_criteria_as_done",
            "Mark a criteria as completed",
        )
        self.add_section("criteria_number", True, "Number of the criteria to mark as done")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Mark criteria as done"""
        current_node = context.current_node

        # Get criteria list
        criteria_list = current_node.get_criteria()
        index = args["index"]

        # Check if index is valid
        if index < 0 or index >= len(criteria_list):
            context.add_command_output(self.name, args, f"Error: Criteria {args['criteria_number']} not found.")
            return

        # Update the criterion's completed status
        criteria_list[index].is_completed = True

        # Add confirmation output
        context.add_command_output(self.name, args, f"Criteria {args['criteria_number']} marked as done.")

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert criteria_number to zero-based index"""
        if "criteria_number" in args:
            args["index"] = int(args["criteria_number"]) - 1  # Convert to 0-based index
        return args

    def validate(self, args: dict[str, Any]) -> list[str]:
        """Validate criteria number"""
        errors = super().validate(args)
        if "criteria_number" in args:
            try:
                index = int(args["criteria_number"]) - 1
                if index < 0:
                    errors.append(f"Criteria index must be positive, got: {index + 1}")
            except ValueError:
                errors.append(f"Invalid criteria index: '{args['criteria_number']}', must be a number")
        return errors


class AddSubproblemCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "add_subproblem",
            "Add a subproblem to the current problem",
        )
        self.add_section("title", True, "Title of the subproblem")
        self.add_section("content", True, "Content of the subproblem definition")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Add a subproblem to the current problem"""
        current_node = context.current_node

        # Check if subproblem with this title already exists
        title = args["title"]
        for child in current_node.list_child_nodes():
            if child.get_title() == title:
                return

        # Create the child node using the encapsulated method
        current_node.create_child_node(title=title, problem_content=args["content"])

        # Add confirmation output
        context.add_command_output(self.name, args, f"Subproblem '{title}' added.")


class AddArtifactCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "add_artifact",
            "Add an artifact to the current problem. Artifacts are closed by default and show only the summary. "
            "Keep content ~1 page long unless specifically requested to be longer. "
            "Use descriptive names that clearly indicate purpose.",
        )
        self.add_section(
            "name", True, "Name of the artifact (use descriptive names like 'Market_Analysis_Summary' not 'Doc1')"
        )
        self.add_section(
            "content", True, "Content of the artifact (keep to ~1 page unless specifically requested to be longer)"
        )
        self.add_section(
            "short_summary",
            True,
            "Short summary of the artifact. Can be 1-2 paragraphs, should call out what's important in this artifact.",
        )

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Add an artifact to the current problem"""
        current_node = context.current_node

        artifact = Artifact(
            name=args["name"],
            content=args["content"],
            short_summary=args["short_summary"],
            is_external=False,
        )
        current_node.add_artifact(artifact)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Artifact '{args['name']}' added.")


class AppendToProblemDefinitionCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "append_to_problem_definition",
            "Append content to the current problem definition",
        )
        self.add_section("content", True, "Content to append")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Append to the problem definition"""
        current_node = context.current_node

        current_node.append_to_problem_definition(args["content"])

        # Add confirmation output
        context.add_command_output(self.name, args, "Problem definition updated.")


class AddCriteriaToSubproblemCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "add_criteria_to_subproblem",
            "Add criteria to a subproblem",
        )
        self.add_section("title", True, "Title of the subproblem")
        self.add_section("criteria", True, "Criteria text")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Add criteria to a subproblem"""
        current_node = context.current_node

        # Get the subproblem by title
        title = args["title"]
        child_nodes = current_node.list_child_nodes()

        # Find the child node with matching title
        subproblem = None
        for child in child_nodes:
            if child.get_title() == title:
                subproblem = child
                break

        if not subproblem:
            return

        # Add criteria to the subproblem
        criteria_text = args["criteria"]
        existing_criteria = [c.content for c in subproblem.get_criteria()]
        if criteria_text in existing_criteria:
            return

        # Create and add criterion
        criterion = Criterion(content=criteria_text)
        subproblem.add_criterion(criterion)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Criteria added to subproblem '{title}'.")


class ActivateSubproblems(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "activate_subproblems",
            "Activate subproblems to run in parallel. Multiple titles can be specified.",
        )
        self.add_section("title", True, "Title of the subproblem to activate", allow_multiple=True)

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Activate subproblems for parallel execution"""
        titles = args["title"]
        if not isinstance(titles, list):
            titles = [titles]

        if not titles:
            raise ValueError("No subproblems specified to activate")

        current_node = context.current_node
        child_node_titles = {node.get_title() for node in current_node.list_child_nodes()}

        # Validate and queue subproblems for parallel activation
        for title in titles:
            if title not in child_node_titles:
                raise ValueError(f"Subproblem '{title}' not found")

        for title in titles:
            # Activate each subproblem without waiting
            result = context.activate_subtask(title)
            if not result:
                raise ValueError(f"Failed to activate subproblem '{title}'")

        context.add_command_output(
            self.name,
            args,
            f"Activated subproblems for parallel execution: {', '.join(titles)}.",
        )


class WaitForSubproblems(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "wait_for_subproblems",
            "Wait for specific subproblems to complete before continuing.",
        )
        self.add_section("title", True, "Title of the subproblem to wait for", allow_multiple=True)

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Wait for specified subproblems to complete"""
        titles = args["title"]
        if not isinstance(titles, list):
            titles = [titles]

        if not titles:
            raise ValueError("No subproblems specified to wait for")

        current_node = context.current_node
        child_nodes = current_node.list_child_nodes()
        active_titles = {
            node.get_title()
            for node in child_nodes
            if node.get_problem_status() not in {ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED}
        }

        # Validate all specified subproblems exist and are active
        for title in titles:
            if title not in active_titles:
                raise ValueError(f"Subproblem '{title}' not found or not active")

        for title in titles:
            context.wait_for_subtask(title)

        context.add_command_output(
            self.name,
            args,
            f"Waiting for subproblems to complete: {', '.join(titles)}.",
        )


class FinishCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "finish_problem",
            help_text=textwrap.dedent("""\
            Finish the current problem. If there is a parent problem, it will become activated.
            You can optionally provide a message to the parent task using the ///message section.
            Ensure other commands are processed before sending this.
            Example with message:
            <<< finish_problem
            ///message
            Completed sub-analysis X, results attached in artifact Y.
            >>>
            Example without message:
            <<< finish_problem
            >>>
            """),
        )
        # Add the optional message section
        self.add_section(
            "message",
            required=False,
            help_text="Optional message to pass to the parent task upon completion.",
        )

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Focus up to the parent problem, potentially passing a message."""
        # Get the optional message from args
        completion_message = args.get("message")

        # Pass the message to the context method
        result = context.finish_node(message=completion_message)

        if not result:
            raise ValueError("Failed to focus up to parent problem.")


class FailCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "fail_problem",
            help_text=textwrap.dedent("""\
            Mark the current problem as FAILED. If there is a parent problem, it will become activated.
            You can optionally provide a message to the parent task using the ///message section explaining the failure.
            Ensure other commands are processed before sending this.
            Example with message:
            <<< fail_problem
            ///message
            Could not proceed due to missing external data source X.
            >>>
            Example without message:
            <<< fail_problem
            >>>
            """),
        )
        # Add the optional message section
        self.add_section(
            "message",
            required=False,
            help_text="Optional message to pass to the parent task explaining the failure.",
        )

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Mark problem as failed and focus up, potentially passing a message."""
        # Get the optional message from args
        failure_message = args.get("message")

        # Pass the message to the context method
        result = context.fail_node(message=failure_message)

        if not result:
            # Keep existing error handling, refine slightly for root node case
            current_node_title = context.current_node.get_title()
            if not context.current_node.get_parent():
                # Specific error if it's the root node trying to fail with a message meant for a parent
                if failure_message:
                    raise ValueError(f"Cannot pass a failure message from the root node '{current_node_title}' as there is no parent.")
                # else: Standard fail for root is handled by context.fail_and_focus_up returning True and engine setting finished=True
            else:
                # General failure case if not root or root without message
                raise ValueError(f"Failed to mark problem as failed and focus up from node '{current_node_title}'.")


class CancelSubproblemCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "cancel_subproblem",
            "Mark a subproblem as cancelled, if you no longer want to start it. It's a way to delete a subtask "
            "that you created but haven't yet started.",
        )
        self.add_section("title", True, "Title of the subproblem to cancel")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Cancel a subproblem"""
        current_node = context.current_node

        # Get the subproblem by title
        title = args["title"]
        child_nodes = current_node.list_child_nodes()

        # Find the child node with matching title
        target_child = None
        for child in child_nodes:
            if child.get_title() == title:
                target_child = child
                break

        if not target_child:
            raise ValueError(f"Subproblem '{title}' not found")

        # Mark the subproblem as cancelled
        target_child.set_problem_status(ProblemStatus.CANCELLED)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Subproblem '{title}' cancelled.")


class AddLogEntryCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "add_log_entry",
            "Add an entry to the permanent log",
        )
        self.add_section("content", True, "Content of the log entry")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Add a log entry"""
        content = args.get("content", "")
        if content:
            context.add_to_permanent_log(content)
            # Add confirmation output
            context.add_command_output(self.name, args, "Log entry added.")


class OpenArtifactCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "open_artifact",
            "Open an artifact to view its full content. Artifacts automatically close after 5 message iterations.",
        )
        self.add_section("name", True, "Name of the artifact to open")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Execute the command to open an artifact"""
        artifact_name = args["name"]

        # Find the artifact in the current node or its ancestors
        current_node = context.current_node

        node_and_artifacts = context.search_artifacts(artifact_name)

        for _, artifact in node_and_artifacts:
            current_node.set_artifact_status(artifact, True)

        context.add_command_output(
            self.name,
            args,
            f"Artifact '{artifact_name}' is now fully visible.",
        )


class CloseArtifactCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "close_artifact",
            "Close an artifact manually, the short summary will remain visible. Artifacts also auto-close after 5 message iterations.",
        )
        self.add_section("name", True, "Name of the artifact to close")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Execute the command to half-close an artifact"""
        artifact_name = args["name"]

        # Find the artifact in the current node or its ancestors
        current_node = context.current_node

        node_and_artifacts = context.search_artifacts(artifact_name)

        for _, artifact in node_and_artifacts:
            current_node.set_artifact_status(artifact, False)

        # For now, just report that the artifact is half-closed
        context.add_command_output(
            self.name,
            args,
            f"Artifact '{artifact_name}' is now closed (showing only the summary).",
        )


class ThinkCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "think",
            "A place for you to think before taking actions",
        )
        self.add_section("content", False, "Thinking content, as long as needed")

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """This is a dummy command that doesn't trigger any actions"""
        # This command doesn't do anything, it's just a place for the assistant to think
        # No output needed for think command
        pass


class AddKnowledgeCommand(BaseCommand[CommandContextImpl]):
    def __init__(self):
        super().__init__(
            "add_knowledge",
            "Add an entry to the shared knowledge base for all assistants.",
        )
        self.add_section("content", True, "The main content of the knowledge entry.")
        self.add_section("title", True, "Optional short title/summary for the entry.")
        self.add_section(
            "tag",
            False,
            "Optional tag for categorization (can be used multiple times).",
            allow_multiple=True,
        )

    def execute(self, context: CommandContextImpl, args: dict[str, Any]) -> None:
        """Add an entry to the shared knowledge base."""
        current_node = context.current_node

        tags = args.get("tag", [])
        # Ensure tags is a list, even if only one is provided
        if isinstance(tags, str):
            tags = [tags]

        entry = KnowledgeEntry(
            content=args["content"],
            author_node_title=current_node.get_title(),
            title=args["title"],
            tags=tags,
        )

        # Add the knowledge entry via the context
        context.add_knowledge_entry(entry)
        # Provide confirmation output using context
        entry_identifier = f"'{entry.title}'" if entry.title else "entry"
        context.add_command_output(self.name, args, f"Knowledge {entry_identifier} added successfully.")


def register_deep_research_commands(registry: CommandRegistry):
    """Registers all built-in Deep Research commands to the given registry."""
    commands_to_register = [
        AddCriteriaCommand(),
        MarkCriteriaAsDoneCommand(),
        AddSubproblemCommand(),
        AddArtifactCommand(),
        AppendToProblemDefinitionCommand(),
        AddCriteriaToSubproblemCommand(),
        ActivateSubproblems(),
        WaitForSubproblems(),
        FinishCommand(),
        FailCommand(),
        CancelSubproblemCommand(),
        AddLogEntryCommand(),
        OpenArtifactCommand(),
        CloseArtifactCommand(),
        ThinkCommand(),
        AddKnowledgeCommand(),
    ]
    for cmd in commands_to_register:
        registry.register(cmd)
