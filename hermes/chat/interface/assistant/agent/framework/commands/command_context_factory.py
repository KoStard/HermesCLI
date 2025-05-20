from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from hermes.chat.interface.assistant.agent.framework.commands.command_context import CommandContext

CommandContextType = TypeVar("CommandContextType", bound=CommandContext)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor


class CommandContextFactory(ABC, Generic[CommandContextType]):
    @abstractmethod
    def create_command_context(
        self, task_processor: "TaskProcessor", current_task_tree_node: "TaskTreeNode", command_processor: "CommandProcessor"
    ) -> CommandContextType:
        pass
