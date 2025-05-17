from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from hermes.chat.interface.assistant.agent.framework.commands.command_context import CommandContext

CommandContextType = TypeVar('CommandContextType', bound=CommandContext)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.engine import AgentEngine
    from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode


class CommandContextFactory(ABC, Generic[CommandContextType]):
    @abstractmethod
    def create_command_context(self, engine: "AgentEngine", current_state_machine_node: "TaskTreeNode") -> CommandContextType:
        pass
