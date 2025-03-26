from typing import Dict, Any, List

from .command import Command, CommandType, register_command, DefineCommand
from .file_system import Artifact, ProblemStatus
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
        root_node = context.file_system.create_root_problem(
            args["title"], args["content"]
        )

        # Set the root node status to CURRENT
        root_node.status = ProblemStatus.IN_PROGRESS

        # Ensure file system is fully updated
        context.update_files()

        # Set problem_defined flag
        context.set_problem_defined(True)

        # Initialize the task executor with the root node
        context.activate_node(root_node)


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

        # Create artifact with default half-closed visibility
        artifact = Artifact(
            name=args["name"], content=args["content"], is_fully_visible=False
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
            "focus_down",
            "Focus on a subproblem",
        )
        self.add_section("title", True, "Title of the subproblem to focus on")

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Focus down to a subproblem"""
        title = args["title"]
        result = context.focus_down(title)

        if not result:
            raise ValueError(
                f"Failed to focus down to subproblem '{title}'. Make sure the subproblem exists."
            )

    def should_be_last_in_message(self):
        return True


@register_command
class FocusUpCommand(Command):
    def __init__(self):
        super().__init__(
            "focus_up",
            "Focus up to the parent problem; when executed on the root problem, will finish the whole task",
            CommandType.SIMPLE,
        )

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Focus up to the parent problem"""
        result = context.focus_up()
        
        if not result:
            raise ValueError("Failed to focus up to parent problem.")

    def should_be_last_in_message(self):
        return True


@register_command
class FailProblemAndFocusUpCommand(Command):
    def __init__(self):
        super().__init__(
            "fail_problem_and_focus_up",
            "Mark the current problem as failed and focus up to the parent problem",
            CommandType.SIMPLE,
        )

    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Mark problem as failed and focus up"""
        result = context.fail_and_focus_up()
        
        if not result:
            raise ValueError("Failed to mark problem as failed and focus up.")

    def should_be_last_in_message(self):
        return True


@register_command
class CancelSubproblemCommand(Command):
    def __init__(self):
        super().__init__(
            "cancel_subproblem",
            "Mark a subproblem as cancelled",
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
            current_node.artifacts[artifact_name].is_fully_visible = True
            self.add_output(
                context,
                args,
                f"Artifact '{artifact_name}' is now fully visible.",
            )
            context.update_files()
            return

        # Check parent chain
        parent_chain = context.file_system.get_parent_chain(current_node)
        for node in parent_chain:
            if artifact_name in node.artifacts:
                node.artifacts[artifact_name].is_fully_visible = True
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
                    subproblem.artifacts[artifact_name].is_fully_visible = True
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
            current_node.artifacts[artifact_name].is_fully_visible = False
            self.add_output(
                context,
                args,
                f"Artifact '{artifact_name}' is now half-closed (showing first 10 lines only).",
            )
            context.update_files()
            return

        # Check parent chain
        parent_chain = context.file_system.get_parent_chain(current_node)
        for node in parent_chain:
            if artifact_name in node.artifacts:
                node.artifacts[artifact_name].is_fully_visible = False
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
                    subproblem.artifacts[artifact_name].is_fully_visible = False
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
