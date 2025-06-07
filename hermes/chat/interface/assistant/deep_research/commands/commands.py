
from hermes.chat.interface.commands.command import CommandRegistry

from .activate_subproblems_command import ActivateSubproblems
from .add_artifact_command import AddArtifactCommand

# Import all commands
from .add_criteria_command import AddCriteriaCommand
from .add_criteria_to_subproblem_command import AddCriteriaToSubproblemCommand
from .add_knowledge_command import AddKnowledgeCommand
from .add_log_entry_command import AddLogEntryCommand
from .add_subproblem_command import AddSubproblemCommand
from .append_knowledge_command import AppendKnowledgeCommand
from .append_to_problem_definition_command import AppendToProblemDefinitionCommand
from .cancel_subproblem_command import CancelSubproblemCommand
from .close_artifact_command import CloseArtifactCommand
from .delete_knowledge_command import DeleteKnowledgeCommand
from .fail_command import FailCommand
from .finish_command import FinishCommand
from .mark_criteria_as_done_command import MarkCriteriaAsDoneCommand
from .open_artifact_command import OpenArtifactCommand
from .rewrite_knowledge_command import RewriteKnowledgeCommand
from .think_command import ThinkCommand
from .wait_for_subproblems_command import WaitForSubproblems


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
        AppendKnowledgeCommand(),
        RewriteKnowledgeCommand(),
        DeleteKnowledgeCommand(),
    ]
    for cmd in commands_to_register:
        registry.register(cmd)
