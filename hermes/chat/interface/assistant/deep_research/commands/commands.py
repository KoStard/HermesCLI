from typing import Any

from hermes.chat.interface.commands.command import CommandRegistry

# Import all commands
from .add_criteria_command import AddCriteriaCommand
from .mark_criteria_as_done_command import MarkCriteriaAsDoneCommand
from .add_subproblem_command import AddSubproblemCommand
from .add_artifact_command import AddArtifactCommand
from .append_to_problem_definition_command import AppendToProblemDefinitionCommand
from .add_criteria_to_subproblem_command import AddCriteriaToSubproblemCommand
from .activate_subproblems_command import ActivateSubproblems
from .wait_for_subproblems_command import WaitForSubproblems
from .finish_command import FinishCommand
from .fail_command import FailCommand
from .cancel_subproblem_command import CancelSubproblemCommand
from .add_log_entry_command import AddLogEntryCommand
from .open_artifact_command import OpenArtifactCommand
from .close_artifact_command import CloseArtifactCommand
from .think_command import ThinkCommand
from .add_knowledge_command import AddKnowledgeCommand
from .append_knowledge_command import AppendKnowledgeCommand
from .rewrite_knowledge_command import RewriteKnowledgeCommand
from .delete_knowledge_command import DeleteKnowledgeCommand


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
