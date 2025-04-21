import textwrap
from typing import Dict, Any, List

from .command import Command, register_command, DefineCommand
from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import Artifact, ProblemStatus
from hermes.interface.assistant.deep_research_assistant.engine.files.knowledge_entry import KnowledgeEntry
from .command_context import CommandContext


@register_command
class DefineProblemCommand(DefineCommand):
    def __init__(self):
        super().__init__(
            "define_problem",
            "Define the initial problem to research",
        )
        self.add_section("title", True, "Title of the problem")
        self.add_section("content", True, "Content of the problem definition")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Create the root problem"""
        context.file_system.create_root_problem(args["title"], args["content"])

        # Ensure file system is fully updated
        context.update_files()


@register_command
class AddCriteriaCommand(Command):
    def __init__(self):
        super().__init__(
            "add_criteria",
            "Add criteria for the current problem",
        )
        self.add_section("criteria", True, "Criteria text")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Add criteria to the current problem"""
        current_node = context.current_node
        if not current_node:
            return

        # Check if criteria already exists
        criteria_text = args["criteria"]
        if criteria_text in current_node.criteria:
            return

        current_node.add_criteria(criteria_text)
        context.update_files()


@register_command
class MarkCriteriaAsDoneCommand(Command):
    def __init__(self):
        super().__init__(
            "mark_criteria_as_done",
            "Mark a criteria as completed",
        )
        self.add_section(
            "criteria_number", True, "Number of the criteria to mark as done"
        )

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Mark criteria as done"""
        current_node = context.current_node
        if not current_node:
            return

        success = current_node.mark_criteria_as_done(args["index"])
        if success:
            context.update_files()

    def transform_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Convert criteria_number to zero-based index"""
        if "criteria_number" in args:
            try:
                args["index"] = (
                    int(args["criteria_number"]) - 1
                )  # Convert to 0-based index
            except ValueError:
                pass  # This will be caught in validation
        return args

    def validate(self, args: Dict[str, Any]) -> List[str]:
        """Validate criteria number"""
        errors = super().validate(args)
        if "criteria_number" in args:
            try:
                index = int(args["criteria_number"]) - 1
                if index < 0:
                    errors.append(f"Criteria index must be positive, got: {index + 1}")
            except ValueError:
                errors.append(
                    f"Invalid criteria index: '{args['criteria_number']}', must be a number"
                )
        return errors


@register_command
class AddSubproblemCommand(Command):
    def __init__(self):
        super().__init__(
            "add_subproblem",
            "Add a subproblem to the current problem",
        )
        self.add_section("title", True, "Title of the subproblem")
        self.add_section("content", True, "Content of the subproblem definition")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Add a subproblem to the current problem"""
        current_node = context.current_node
        if not current_node:
            return

        # Check if subproblem with this title already exists
        title = args["title"]
        if title in current_node.subproblems:
            return

        subproblem = current_node.add_subproblem(title, args["content"])
        # Set initial status to NOT_STARTED
        subproblem.status = ProblemStatus.NOT_STARTED
        # Create directories for the new subproblem
        context.file_system._create_node_directories(subproblem)
        context.update_files()


@register_command
class AddArtifactCommand(Command):
    def __init__(self):
        super().__init__(
            "add_artifact",
            "Add an artifact to the current problem",
        )
        self.add_section("name", True, "Name of the artifact")
        self.add_section("content", True, "Content of the artifact")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Add an artifact to the current problem"""
        current_node = context.current_node
        if not current_node:
            return

        artifact = Artifact(
            name=args["name"], content=args["content"], is_external=True
        )
        current_node.artifacts[args["name"]] = artifact
        context.update_files()


@register_command
class AppendToProblemDefinitionCommand(Command):
    def __init__(self):
        super().__init__(
            "append_to_problem_definition",
            "Append content to the current problem definition",
        )
        self.add_section("content", True, "Content to append")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Append to the problem definition"""
        current_node = context.current_node
        if not current_node:
            return

        current_node.append_to_problem_definition(args["content"])
        context.update_files()


@register_command
class AddCriteriaToSubproblemCommand(Command):
    def __init__(self):
        super().__init__(
            "add_criteria_to_subproblem",
            "Add criteria to a subproblem",
        )
        self.add_section("title", True, "Title of the subproblem")
        self.add_section("criteria", True, "Criteria text")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Add criteria to a subproblem"""
        current_node = context.current_node
        if not current_node:
            return

        # Get the subproblem by title
        title = args["title"]
        if title not in current_node.subproblems:
            return

        subproblem = current_node.subproblems[title]

        # Add criteria to the subproblem
        criteria_text = args["criteria"]
        if criteria_text in subproblem.criteria:
            return

        subproblem.add_criteria(criteria_text)
        context.update_files()


@register_command
class FocusDownCommand(Command):
    def __init__(self):
        super().__init__(
            "activate_subproblems_and_wait",
            "Activate subproblems and wait for them to be finished before continuing. Multiple titles are allowed, they will be executed sequentially.",
        )
        self.add_section("title", True, "Title of the subproblem to activate", allow_multiple=True)

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Focus down to a subproblem"""
        titles = args["title"]
        if not isinstance(titles, list):
            titles = [titles]  # Handle single title case
            
        if not titles:
            raise ValueError("No subproblems specified to activate")

        # Queue up all subproblems for sequential activation
        current_node = context.current_node
        if not current_node:
            raise ValueError("No current node")

        # Validate all subproblems exist before queueing
        for title in titles:
            if title not in current_node.subproblems:
                raise ValueError(f"Subproblem '{title}' not found")

        # Add all titles to the queue except the first one
        if len(titles) > 1:
            context.children_queue[current_node.title].extend(titles[1:])

        self.add_output(
            context,
            args,
            f"Focusing on {titles[0]}.",
        )

        # Activate the first subproblem
        result = context.focus_down(titles[0])
        if not result:
            raise ValueError(
                f"Failed to activate subproblem '{titles[0]}'. Make sure the subproblem exists."
            )

    def should_be_last_in_message(self):
        return True


@register_command
class FocusUpCommand(Command):
    def __init__(self):
        # Change to BLOCK type and update help text
        super().__init__(
            "finish_problem",
            help_text=textwrap.dedent("""\
            Finish the current problem. If there is a parent problem, it will become activated.
            You can optionally provide a message to the parent task using the ///message section.
            Ensure other commands are processed before sending this.
            Example with message:
            <<< finish_problem
            /// message
            Completed sub-analysis X, results attached in artifact Y.
            >>>
            Example without message:
            <<< finish_problem
            >>>
            """)
        )
        # Add the optional message section
        self.add_section("message", required=False, help_text="Optional message to pass to the parent task upon completion.")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Focus up to the parent problem, potentially passing a message."""
        # Get the optional message from args
        completion_message = args.get("message")

        # Pass the message to the context method
        result = context.focus_up(message=completion_message)

        if not result:
            raise ValueError("Failed to focus up to parent problem.")

    def should_be_last_in_message(self):
        # This command changes focus, so it should still be last
        return True


@register_command
class FailProblemAndFocusUpCommand(Command):
    def __init__(self):
        super().__init__(
            "fail_problem",
            help_text=textwrap.dedent("""\
            Mark the current problem as FAILED. If there is a parent problem, it will become activated.
            You can optionally provide a message to the parent task using the ///message section explaining the failure.
            Ensure other commands are processed before sending this.
            Example with message:
            <<< fail_problem
            /// message
            Could not proceed due to missing external data source X.
            >>>
            Example without message:
            <<< fail_problem
            >>>
            """),
        )
        # Add the optional message section
        self.add_section("message", required=False, help_text="Optional message to pass to the parent task explaining the failure.")


    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Mark problem as failed and focus up, potentially passing a message."""
        # Get the optional message from args
        failure_message = args.get("message")

        # Pass the message to the context method
        result = context.fail_and_focus_up(message=failure_message)

        if not result:
            # Keep existing error handling, refine slightly for root node case
            current_node_title = context.current_node.title if context.current_node else "Unknown"
            if context.current_node and not context.current_node.parent:
                 # Specific error if it's the root node trying to fail with a message meant for a parent
                 if failure_message:
                      raise ValueError(f"Cannot pass a failure message from the root node '{current_node_title}' as there is no parent.")
                 # else: Standard fail for root is handled by context.fail_and_focus_up returning True and engine setting finished=True
            else:
                 # General failure case if not root or root without message
                 raise ValueError(f"Failed to mark problem as failed and focus up from node '{current_node_title}'.")

    def should_be_last_in_message(self):
        return True


@register_command
class CancelSubproblemCommand(Command):
    def __init__(self):
        super().__init__(
            "cancel_subproblem",
            "Mark a subproblem as cancelled, if you no longer want to start it. It's a way to delete a subtask that you created but haven't yet started.",
        )
        self.add_section("title", True, "Title of the subproblem to cancel")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Cancel a subproblem"""
        current_node = context.current_node
        if not current_node:
            return

        # Get the subproblem by title
        title = args["title"]
        if title not in current_node.subproblems:
            raise ValueError(f"Subproblem '{title}' not found")

        subproblem = current_node.subproblems[title]

        # Mark the subproblem as cancelled
        subproblem.status = ProblemStatus.CANCELLED

        # Update the file system
        context.update_files()


@register_command
class AddLogEntryCommand(Command):
    def __init__(self):
        super().__init__(
            "add_log_entry",
            "Add an entry to the permanent log",
        )
        self.add_section("content", True, "Content of the log entry")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Add a log entry"""
        content = args.get("content", "")
        if content:
            context.add_to_permanent_log(content)


@register_command
class OpenArtifactCommand(Command):
    def __init__(self):
        super().__init__(
            "open_artifact",
            "Open an artifact to view its full content",
        )
        self.add_section("name", True, "Name of the artifact to open")
        self.add_section("reason", True, "Reason why you need to see the full content")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Execute the command to open an artifact"""
        artifact_name = args.get("name", "")
        reason = args.get("reason", "")

        # Find the artifact in the current node or its ancestors
        current_node = context.current_node
        if not current_node:
            raise ValueError("No current node")

        # Check current node's artifacts
        if artifact_name in current_node.artifacts:
            # Modify the visibility flag on the *current_node* perspective
            current_node.visible_artifacts[artifact_name] = True
            self.add_output(
                context,
                args,
                f"Artifact '{artifact_name}' is now fully visible.",
            )
            context.update_files()
            return

        # Check parent chain - visibility is controlled by the current node's perspective
        parent_chain = context.file_system.get_parent_chain(current_node)
        for node in parent_chain:
            if artifact_name in node.artifacts:
                # Modify the visibility flag on the *current_node* perspective
                current_node.visible_artifacts[artifact_name] = True
                self.add_output(
                    context,
                    args,
                    f"Artifact '{artifact_name}' is now fully visible.",
                )
                context.update_files()
                return

        # Check all subproblems recursively
        def search_subproblems(node):
            for subproblem in node.subproblems.values():
                if artifact_name in subproblem.artifacts:
                    current_node.visible_artifacts[artifact_name] = True
                    return True
                if search_subproblems(subproblem):
                    return True
            return False

        if search_subproblems(context.file_system.root_node):
            self.add_output(
                context,
                args,
                f"Artifact '{artifact_name}' is now fully visible.",
            )
            context.update_files()
            return

        # If we get here, the artifact wasn't found
        raise ValueError(f"Artifact '{artifact_name}' not found")


@register_command
class HalfCloseArtifactCommand(Command):
    def __init__(self):
        super().__init__(
            "half_close_artifact",
            "Half-close an artifact to show only the first 10 lines",
        )
        self.add_section("name", True, "Name of the artifact to half-close")
        self.add_section("reason", True, "Reason why you're half-closing this artifact")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Execute the command to half-close an artifact"""
        artifact_name = args.get("name", "")
        reason = args.get("reason", "")

        # Find the artifact in the current node or its ancestors
        current_node = context.current_node
        if not current_node:
            raise ValueError("No current node")

        # Check current node's artifacts
        if artifact_name in current_node.artifacts:
            # Modify the visibility flag on the *current_node* perspective
            current_node.visible_artifacts[artifact_name] = False
            self.add_output(
                context,
                args,
                f"Artifact '{artifact_name}' is now half-closed (showing first 10 lines only).",
            )
            context.update_files()
            return

        # Check parent chain - visibility is controlled by the current node's perspective
        parent_chain = context.file_system.get_parent_chain(current_node)
        for node in parent_chain:
            if artifact_name in node.artifacts:
                # Modify the visibility flag on the *current_node* perspective
                current_node.visible_artifacts[artifact_name] = False
                self.add_output(
                    context,
                    args,
                    f"Artifact '{artifact_name}' is now half-closed (showing first 10 lines only).",
                )
                context.update_files()
                return

        # Check all subproblems recursively
        def search_subproblems(node):
            for subproblem in node.subproblems.values():
                if artifact_name in subproblem.artifacts:
                    current_node.visible_artifacts[artifact_name] = False
                    return True
                if search_subproblems(subproblem):
                    return True
            return False

        if search_subproblems(context.file_system.root_node):
            self.add_output(
                context,
                args,
                f"Artifact '{artifact_name}' is now half-closed (showing first 10 lines only).",
            )
            context.update_files()
            return

        # If we get here, the artifact wasn't found
        raise ValueError(f"Artifact '{artifact_name}' not found")


@register_command
class ThinkCommand(Command):
    def __init__(self):
        super().__init__(
            "think",
            "A place for you to think before taking actions",
        )
        self.add_section("content", False, "Thinking content, as long as needed")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """This is a dummy command that doesn't trigger any actions"""
        # This command doesn't do anything, it's just a place for the assistant to think
        pass


@register_command
class AddKnowledgeCommand(Command):
    def __init__(self):
        super().__init__(
            "add_knowledge",
            "Add an entry to the shared knowledge base for all assistants."
        )
        self.add_section("content", True, "The main content of the knowledge entry.")
        self.add_section("title", False, "Optional short title/summary for the entry.")
        self.add_section("tag", False, "Optional tag for categorization (can be used multiple times).", allow_multiple=True)

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Add an entry to the shared knowledge base."""
        current_node = context.current_node
        if not current_node:
            # Should ideally not happen if a problem is defined, but good practice
            self.add_output(context, args, {"output": "Error: Cannot add knowledge without an active problem node."})
            return

        tags = args.get("tag", [])
        # Ensure tags is a list, even if only one is provided
        if isinstance(tags, str):
            tags = [tags]

        entry = KnowledgeEntry(
            content=args.get("content"),
            author_node_title=current_node.title,
            title=args.get("title"),
            tags=tags
        )

        context.file_system.add_knowledge_entry(entry)
        # Provide confirmation output
        entry_identifier = f"'{entry.title}'" if entry.title else "entry"
        self.add_output(context, args, {"output": f"Knowledge {entry_identifier} added successfully."})


def register_predefined_commands():
    # This function ensures that the command classes are imported and thus registered
    # by the @register_command decorator when this module is imported.
    pass
